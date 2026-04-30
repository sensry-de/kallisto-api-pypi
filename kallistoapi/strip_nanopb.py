import re
import sys
from pathlib import Path

def strip_nanopb(proto_text: str) -> str:
    # 1. Remove nanopb import lines
    proto_text = re.sub(
        r'^\s*import\s+"nanopb\.proto";\s*\n',
        '',
        proto_text,
        flags=re.MULTILINE
    )

    # 2. Remove nanopb field options like:
    # [(nanopb).int_size = IS_16]
    # or inside multiple options:
    # [(.nanopb).foo = bar, (nanopb).int_size = IS_16]
    def clean_options(match):
        content = match.group(1)

        # Remove nanopb options inside brackets
        cleaned = re.sub(
            r'\(?\s*nanopb\s*\)\s*\.\s*\w+\s*=\s*[^,\]]+',
            '',
            content
        )

        # Clean leftover commas and whitespace
        cleaned = re.sub(r',\s*,', ',', cleaned)
        cleaned = cleaned.strip().strip(',')

        return f"[{cleaned}]" if cleaned else ''

    proto_text = re.sub(
        r'\[([^\]]+)\]',
        clean_options,
        proto_text
    )

    # 3. Remove empty brackets left behind
    proto_text = re.sub(r'\[\s*\]', '', proto_text)

    # 4. Clean trailing spaces
    proto_text = re.sub(r'[ \t]+$', '', proto_text, flags=re.MULTILINE)

    return proto_text


def main():
    if len(sys.argv) != 3:
        print("Usage: python strip_nanopb.py input.proto output.proto")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    text = input_path.read_text()
    cleaned = strip_nanopb(text)
    output_path.write_text(cleaned)

    print(f"Written cleaned proto to: {output_path}")


if __name__ == "__main__":
    main()
