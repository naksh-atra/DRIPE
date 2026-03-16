import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChangelogGenerator:
    def __init__(self):
        pass

    def generate_markdown(self, version: str, diff_stats: dict) -> str:
        """
        Produces a human-readable markdown changelog.
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        changelog = f"# DRIPE Changelog - {version}\n"
        changelog += f"**Date:** {date_str}\n\n"
        
        changelog += "## Graph Statistics\n"
        changelog += f"- **Edges Added:** {diff_stats.get('added', 0)}\n"
        changelog += f"- **Edges Removed:** {diff_stats.get('removed', 0)}\n"
        changelog += f"- **Confidence Updates:** {diff_stats.get('modified', 0)}\n\n"
        
        changelog += "## Benchmark Performance\n"
        changelog += f"- **Recall@10:** {diff_stats.get('recall_10', 'N/A')}\n"
        changelog += f"- **MRR:** {diff_stats.get('mrr', 'N/A')}\n\n"
        
        changelog += "## Data Source Highlights\n"
        for src, count in diff_stats.get('sources', {}).items():
            changelog += f"- **{src}:** {count} new relationships\n"
            
        return changelog

    def save_changelog(self, version: str, content: str):
        filename = f"CHANGELOG_{version.replace('.', '_')}.md"
        with open(filename, 'w') as f:
            f.write(content)
        logger.info(f"Changelog saved to {filename}")
