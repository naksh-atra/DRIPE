import os
import tarfile
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SnapshotManager:
    def __init__(self, snapshot_dir: str = "snapshots"):
        self.snapshot_dir = snapshot_dir
        self.manifest_path = os.path.join(snapshot_dir, "manifest.json")
        os.makedirs(snapshot_dir, exist_ok=True)
        self._init_manifest()

    def _init_manifest(self):
        if not os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'w') as f:
                json.dump({"snapshots": []}, f)

    def create_snapshot(self, version: str, files_to_archive: list):
        """
        Compresses graph data and FAISS index into a versioned tar.gz archive.
        Updates manifest.json.
        """
        archive_name = f"dripe_snapshot_{version}.tar.gz"
        archive_path = os.path.join(self.snapshot_dir, archive_name)
        
        with tarfile.open(archive_path, "w:gz") as tar:
            for f in files_to_archive:
                if os.path.exists(f):
                    tar.add(f, arcname=os.path.basename(f))
        
        # Update Manifest
        with open(self.manifest_path, 'r+') as f:
            data = json.load(f)
            data["snapshots"].append({
                "version": version,
                "timestamp": datetime.utcnow().isoformat(),
                "archive": archive_name,
                "benchmarked": False
            })
            f.seek(0)
            json.dump(data, f, indent=4)
            
        logger.info(f"Snapshot created: {archive_name}")
        return archive_path
