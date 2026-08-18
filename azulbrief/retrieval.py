import json, math, re
from collections import Counter
from pathlib import Path

def tokens(text): return re.findall(r"[a-z0-9]+", text.lower())
class ProductRetriever:
    def __init__(self, path="data/azul_corpus.json"):
        self.docs=json.loads(Path(path).read_text(encoding="utf-8"))
        self.corpus=[tokens(d["text"]) for d in self.docs]
        self.avgdl=sum(map(len,self.corpus))/len(self.corpus)
    def search(self, query:str, k=3):
        q=tokens(query); n=len(self.corpus); dfs=Counter(t for doc in self.corpus for t in set(doc))
        scores=[]
        for doc in self.corpus:
            tf=Counter(doc); score=0.0
            for term in q:
                if not tf[term]: continue
                idf=math.log(1+(n-dfs[term]+0.5)/(dfs[term]+0.5))
                score += idf*(tf[term]*2.5)/(tf[term]+1.5*(0.25+0.75*len(doc)/self.avgdl))
            scores.append(score)
        ranked=sorted(zip(scores,self.docs),key=lambda x:x[0],reverse=True)
        return [dict(d,score=float(s)) for s,d in ranked[:k] if s>0]
