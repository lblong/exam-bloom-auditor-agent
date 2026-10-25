from tool.file_parser import parse_file
from tool.bloom_evaluator import evaluate_all

ds = parse_file("data/de_mau.docx")
ket_qua = evaluate_all(ds, limit=3)   # CHỈ 3 câu đầu để tiết kiệm token

tong_in = tong_out = 0
for r in ket_qua:
    print(f"Câu {r.so_cau}: {r.muc_do} (tin cậy {r.do_tin_cay})")
    print(f"   Lý do: {r.ly_do}")
    print(f"   Token: vào={r.input_tokens}, ra={r.output_tokens}")
    tong_in += r.input_tokens
    tong_out += r.output_tokens

print(f"\nTỔNG token: vào={tong_in}, ra={tong_out}, model={ket_qua[0].model}")