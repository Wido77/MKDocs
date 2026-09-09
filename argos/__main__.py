from __future__ import annotations

import argparse

from .config import default_paths
from .database import Database
from .server import make_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor local de Argos")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--data-dir")
    args = parser.parse_args()
    paths = default_paths(args.data_dir)
    paths.ensure()
    database = Database(paths.database)
    database.initialize()
    server = make_server(args.host, args.port, database, paths.artifacts_dir)
    print(f"Argos disponible en http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
