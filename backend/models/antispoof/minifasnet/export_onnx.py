import argparse, os, sys, inspect
from pathlib import Path
import torch

def add_src_to_syspath():
    sf_env = os.getenv("SILENTFACE_SRC")
    if sf_env:
        p = Path(sf_env)
        src = p if p.name == "src" else (p / "src")
        if (src / "model_lib" / "MiniFASNet.py").exists() or (src / "anti_spoofing" / "model_lib" / "MiniFASNet.py").exists():
            sys.path.insert(0, str(src.parent))
            return True
    here = Path(__file__).resolve()
    for base in [here.parent, *list(here.parents)[:5]]:
        cand = base / "src"
        if (cand / "model_lib" / "MiniFASNet.py").exists() or (cand / "anti_spoofing" / "model_lib" / "MiniFASNet.py").exists():
            sys.path.insert(0, str(base))
            return True
    return False

def try_import(*candidates):
    errs=[]
    for mod, cls in candidates:
        try:
            m = __import__(mod, fromlist=[cls])
            return getattr(m, cls)
        except Exception as e:
            errs.append(f"{mod}.{cls}: {e}")
    raise ImportError("Gagal impor kelas MiniFASNet:\n" + "\n".join(errs))

def import_net(arch):
    arch = arch.lower()
    if arch=="v2":
        return try_import(("src.model_lib.MiniFASNet","MiniFASNetV2"),
                          ("src.anti_spoofing.model_lib.MiniFASNet","MiniFASNetV2"))
    # v1se: beberapa fork pakai nama MiniFASNetSE
    return try_import(("src.model_lib.MiniFASNet","MiniFASNetV1SE"),
                      ("src.model_lib.MiniFASNet","MiniFASNetSE"),
                      ("src.anti_spoofing.model_lib.MiniFASNet","MiniFASNetV1SE"),
                      ("src.anti_spoofing.model_lib.MiniFASNet","MiniFASNetSE"))

def detect_num_classes(sd):
    # cari layer klasifikasi: prob/fc/classifier/linear/logits
    cand = []
    for k,v in sd.items():
        if not (hasattr(v,"shape") and v.ndim==2): continue
        out,in_ = v.shape
        name = k.lower()
        score = 0
        if any(t in name for t in ["prob","classifier","fc","linear","logits"]): score += 2
        if in_ in (64,128,256): score += 1
        if out in (2,3): score += 3
        cand.append((score,out,k))
    if not cand:
        return 2
    cand.sort(reverse=True)
    return cand[0][1]

def detect_conv6_kernel(sd):
    # cari depthwise conv terakhir yang sering bernama conv_6_dw.* / conv6_dw.* dengan kernel 5/7
    for k in sorted(sd.keys())[::-1]:
        v = sd[k]
        if hasattr(v,"shape") and v.ndim==4 and k.endswith(".weight"):
            ks = v.shape[-1]
            name = k.lower()
            if ks in (5,7) and ("conv_6" in name or "conv6" in name or "dw" in name):
                return ks
    # fallback: scan semua 4D, pilih yang kernel-nya 5/7 terakhir
    for k in sorted(sd.keys())[::-1]:
        v = sd[k]
        if hasattr(v,"shape") and v.ndim==4 and v.shape[-1] in (5,7):
            return int(v.shape[-1])
    return None

def read_meta(wf):
    state = torch.load(str(wf), map_location="cpu")
    sd = state.get("state_dict", state)
    num_classes = detect_num_classes(sd)
    convk = detect_conv6_kernel(sd)
    return num_classes, convk

def build_model(Net, num_classes, img_size, convk):
    sig = inspect.signature(Net)
    kw = {}
    if "num_classes" in sig.parameters: kw["num_classes"]=num_classes
    elif "classnum" in sig.parameters: kw["classnum"]=num_classes
    if "img_size" in sig.parameters: kw["img_size"]=img_size
    if "img_h" in sig.parameters and "img_w" in sig.parameters:
        kw["img_h"]=img_size; kw["img_w"]=img_size
    if convk and "conv6_kernel" in sig.parameters:
        kw["conv6_kernel"]=(convk,convk)
    print(f"[info] init Net with kwargs={kw}")
    try:
        return Net(**kw)
    except TypeError:
        return Net()

def load_state(model, wf):
    state = torch.load(str(wf), map_location="cpu")
    sd = state.get("state_dict", state)
    clean={}
    for k,v in sd.items():
        kk=k
        for p in ("module.","model."):
            if kk.startswith(p): kk=kk[len(p):]
        clean[kk]=v
    missing, unexpected = model.load_state_dict(clean, strict=False)
    if missing: print("[warn] missing keys:", missing)
    if unexpected: print("[warn] unexpected keys:", unexpected)
    model.eval()
    return model

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights_file", required=True)
    ap.add_argument("--out", default="minifasnet.onnx")
    ap.add_argument("--arch", default="v1se", choices=["v1se","v2"])
    ap.add_argument("--img-size", type=int, default=80)
    ap.add_argument("--force-classes", type=int, default=None)
    ap.add_argument("--force-conv-k", type=int, default=None, choices=[5,7])
    args = ap.parse_args()

    if not add_src_to_syspath():
        print("[hint] Folder 'src' tidak ditemukan. Pastikan SILENTFACE_SRC sudah di-set.")

    Net = import_net(args.arch)
    wf = Path(args.weights_file).resolve()
    if not wf.exists(): raise FileNotFoundError(wf)

    nc, ck = read_meta(wf)
    if args.force_classes: nc = args.force_classes
    if args.force_conv_k: ck = args.force_conv_k
    print(f"[info] checkpoint meta -> num_classes={nc}, conv6_kernel={(ck,ck) if ck else 'default'}")

    model = build_model(Net, nc, args.img_size, ck)
    model = load_state(model, wf)

    dummy = torch.randn(1,3,args.img_size,args.img_size)
    torch.onnx.export(model, dummy, args.out,
        input_names=["input"], output_names=["prob"],
        opset_version=11, dynamic_axes={"input":{0:"N"}, "prob":{0:"N"}}
    )
    print(f"[ok] saved ONNX -> {args.out}")

if __name__ == "__main__":
    main()
