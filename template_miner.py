from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.masking import MaskingInstruction


def build_miner():
    config = TemplateMinerConfig()
    # Replace IP addresses and numbers with placeholders before grouping,
    # so "from 10.0.0.5" and "from 192.168.1.9" are treated as the same thing.
    config.masking_instructions = [
        MaskingInstruction(
            r"((?<=[^A-Za-z0-9])|^)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})((?=[^A-Za-z0-9])|$)",
            "IP",
        ),
        MaskingInstruction(
            r"((?<=[^A-Za-z0-9])|^)([\-\+]?\d+)((?=[^A-Za-z0-9])|$)",
            "NUM",
        ),
    ]
    return TemplateMiner(config=config)


def mine_templates(messages):
    """
    Groups log messages into templates using Drain.
    Returns two lists, each the same length as messages:
      - template_ids: a number identifying each message's template
      - templates: the template text, e.g. "Failed password for <*> from <IP>"
    """
    miner = build_miner()

    template_ids = []
    for msg in messages:
        result = miner.add_log_message(str(msg))
        template_ids.append(result["cluster_id"])

    # Templates can become more general as Drain sees more lines,
    # so read the final version of each one at the end.
    final = {c.cluster_id: c.get_template() for c in miner.drain.clusters}
    templates = [final[tid] for tid in template_ids]

    return template_ids, templates


if __name__ == "__main__":
    # Quick test with sample lines
    sample = [
        "Failed password for root from 10.0.0.5 port 22 ssh2",
        "Failed password for admin from 192.168.1.9 port 4455 ssh2",
        "Accepted password for gurvir from 10.0.0.7 port 22 ssh2",
        "session opened for user root by (uid=0)",
        "session opened for user gurvir by (uid=1000)",
    ]
    ids, temps = mine_templates(sample)
    for line, tid, t in zip(sample, ids, temps):
        print(f"[{tid}] {t}")