"""
AetherKernel: Symbolic Code Property Graph (CPG) Engine
Extracts Abstract Syntax Trees (AST) using Tree-sitter and stores dependency
graphs inside an embedded, in-process KuzuDB database.
"""
import os
import time
from typing import List, Tuple
import kuzu
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

class AetherCPG:
    def __init__(self, db_path: str = "./aether_kuzu_db"):
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()

    def _initialize_schema(self):
        try:
            self.conn.execute(
                "CREATE NODE TABLE Function("
                "name STRING, signature STRING, body STRING, PRIMARY KEY(name));"
            )
            self.conn.execute(
                "CREATE NODE TABLE Module("
                "name STRING, file_path STRING, PRIMARY KEY(name));"
            )
            self.conn.execute("CREATE REL TABLE CALLS(FROM Function TO Function);")
            self.conn.execute("CREATE REL TABLE CONTAINS(FROM Module TO Function);")
        except Exception:
            pass

    def ingest_code(self, module_name: str, file_path: str, code_content: str):
        self.conn.execute(
            "MERGE (m:Module {name: $name}) ON MATCH SET m.file_path = $fp ON CREATE SET m.file_path =$fp;",
            {"name": module_name, "fp": file_path}
        )
        tree = parser.parse(bytes(code_content, "utf8"))
        root = tree.root_node
        for child in root.children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")
                params_node = child.child_by_field_name("parameters")
                func_name = code_content[name_node.start_byte:name_node.end_byte]
                func_sig = code_content[name_node.start_byte:params_node.end_byte]
                func_body = code_content[child.start_byte:child.end_byte]

                self.conn.execute(
                    "MERGE (f:Function {name: $name}) "
                    "ON MATCH SET f.signature = $sig, f.body =$body "
                    "ON CREATE SET f.signature = $sig, f.body =$body;",
                    {"name": func_name, "sig": func_sig, "body": func_body}
                )
                self.conn.execute(
                    "MATCH (m:Module {name: $mname}), (f:Function {name:$fname}) "
                    "CREATE (m)-[:CONTAINS]->(f);",
                    {"mname": module_name, "fname": func_name}
                )

    def extract_deterministic_cag_prefix(self, target_function: str) -> str:
        cypher_query = (
            "MATCH (f:Function {name: $name})-[:CALLS*0..2]->(dep:Function) "
            "RETURN dep.name, dep.signature, dep.body;"
        )
        results = self.conn.execute(cypher_query, {"name": target_function})
        extracted_dependencies: List[Tuple[str, str, str]] = []
        while results.has_next():
            row = results.get_next()
            extracted_dependencies.append((row[0], row[1], row[2]))

        extracted_dependencies.sort(key=lambda item: item[0])
        formatted_blocks = [
            f"# Signature Definition: {dep[1]}\n{dep[2]}"
            for dep in extracted_dependencies
        ]
        return "\n\n".join(formatted_blocks)

if __name__ == "__main__":
    cpg = AetherCPG("./test_kuzu_db")
    sample_code = """
def compute_checksum(payload: str) -> str:
    return hex(hash(payload))

def dispatch_packet(packet_id: str, data: str) -> bool:
    chk = compute_checksum(data)
    return len(chk) > 0
"""
    cpg.ingest_code("network_mod", "/sys/net/packet.py", sample_code)
    prefix = cpg.extract_deterministic_cag_prefix("dispatch_packet")
    print("--- DETERMINISTIC CAG PREFIX ---\n", prefix)
