"""Token counts with the open Llama 4 tokenizer, as a stand-in. Claude's counts differ; use count_tokens on the API for exact numbers."""
import base64, pathlib, urllib.request
import tiktoken

URL = "https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama4/tokenizer.model"
PAT = r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
_ENC = None


def count(text):
    global _ENC
    if _ENC is None:
        f = pathlib.Path(__file__).resolve().parents[1] / "data" / "llama4.model"
        if not f.exists():
            f.parent.mkdir(exist_ok=True)
            urllib.request.urlretrieve(URL, f)
        ranks = {base64.b64decode(a): int(b) for a, b in (l.split() for l in f.read_bytes().splitlines() if l)}
        _ENC = tiktoken.Encoding("llama4", pat_str=PAT, mergeable_ranks=ranks, special_tokens={})
    return len(_ENC.encode_ordinary(text))
