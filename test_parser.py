from tool.file_parser import parse_file

ds = parse_file("data/de_mau.docx")
print(f"Đọc được {len(ds)} câu\n")
for q in ds:
    print(q.model_dump_json(indent=2, ensure_ascii=False))