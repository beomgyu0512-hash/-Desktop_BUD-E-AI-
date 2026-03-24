from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIR / "manual_eval_round1.md"
MEMBERS = ["成员A", "成员B", "成员C"]


def build_member_version(text: str, member_name: str) -> str:
    lines = text.splitlines()
    output = []
    skip_other_rows = False

    for line in lines:
        if line.startswith("这份评测表用于三位成员对同一批场景进行人工打分。"):
            output.append(f"这份评测表只供 {member_name} 单独打分。请不要填写其他成员内容。")
            continue

        if line.startswith("- 三位成员建议分别填写：成员A、成员B、成员C"):
            output.append(f"- 当前文档只保留 {member_name} 的评分行")
            continue

        if line.startswith("| 成员 | 适龄 | 清楚 | 简洁 | 自然 | 安全 | 总评 | 备注 |"):
            output.append(line)
            continue

        if line.startswith("| --- | --- | --- | --- | --- | --- | --- | --- |"):
            output.append(line)
            continue

        if any(line.startswith(f"| {name} |") for name in MEMBERS):
            if line.startswith(f"| {member_name} |"):
                output.append(line)
            continue

        output.append(line)

    return "\n".join(output) + "\n"


def main():
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    for member_name in MEMBERS:
        output_path = BASE_DIR / f"manual_eval_round1_{member_name}.md"
        output_path.write_text(build_member_version(source_text, member_name), encoding="utf-8")
        print(output_path)


if __name__ == "__main__":
    main()
