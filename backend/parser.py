import fitz, re, json, os
from pathlib import Path

TOC_RE = re.compile(r'(?m)^(\d+)\.\s*(.+?)\s+(\d{1,4})\s*$')
Q_RE = re.compile(r'(?m)^(\d+)\.\s+')
OPT_RE = re.compile(r'(?m)^([A-E])\.\s*')
SOL_RE = re.compile(r'(?m)^Solution for Question\s+(\d+)\s*:')
ANS_RE = re.compile(r'Question\s+(\d+)\s+(\d+)')

def clean(s):
    s=s.replace('\u00a0',' ')
    s=re.sub(r'\n{3,}','\n\n',s)
    return s.strip()

def extract_toc(doc):
    toc_text='\n'.join(doc[i].get_text() for i in range(min(4,len(doc))))
    lessons=[]
    for m in TOC_RE.finditer(toc_text):
        n,name,page=m.groups()
        # avoid footer/page patterns by requiring reasonable page and known lesson formatting
        if int(page)>=5 and int(n)<=100:
            lessons.append({'number':int(n),'title':clean(name),'page':int(page)})
    # dedupe
    out=[]; seen=set()
    for x in lessons:
        if x['number'] not in seen:
            out.append(x); seen.add(x['number'])
    out.sort(key=lambda x:x['number'])
    return out

def split_questions(text):
    matches=list(Q_RE.finditer(text))
    blocks=[]
    for i,m in enumerate(matches):
        start=m.start(); end=matches[i+1].start() if i+1<len(matches) else len(text)
        num=int(m.group(1)); body=text[m.end():end].strip()
        if num<=0 or num>500: continue
        blocks.append((num,body))
    return blocks

def parse_question(body):
    opts=list(OPT_RE.finditer(body))
    if not opts:
        return clean(body), []
    q=clean(body[:opts[0].start()])
    options=[]
    for i,m in enumerate(opts):
        end=opts[i+1].start() if i+1<len(opts) else len(body)
        txt=clean(body[m.end():end])
        options.append({'label':m.group(1),'text':txt})
    return q,options

def parse_chapter(doc, lesson, next_page):
    start=lesson['page']-1
    end=(next_page-1 if next_page else len(doc))
    text='\n'.join(doc[i].get_text() for i in range(start,end))
    # cut before answer/solution section for question extraction
    cut=min([p for p in [text.find('Correct Answers'), text.find('Solution for Question')] if p>=0] or [len(text)])
    qtext=text[:cut]
    answers={int(a):int(b) for a,b in ANS_RE.findall(text)}
    raw_all=split_questions(qtext)
    # Keep the first occurrence of each question number. Numbered labels inside
    # image/table matching questions can otherwise look like new questions.
    raw=[]; seen=set()
    expected_max=max(answers.keys(), default=0)
    for item in raw_all:
        num=item[0]
        if num in seen: continue
        if expected_max and num>expected_max: continue
        seen.add(num); raw.append(item)
    # solutions are sequential and may include nested question references; use explicit headers
    sols={}
    sm=list(SOL_RE.finditer(text))
    for i,m in enumerate(sm):
        qn=int(m.group(1)); s=m.end(); e=sm[i+1].start() if i+1<len(sm) else len(text)
        sols[qn]=clean(text[s:e])
    questions=[]
    for num,body in raw:
        q,opts=parse_question(body)
        ans_idx=answers.get(num)
        correct=chr(64+ans_idx) if ans_idx and 1<=ans_idx<=5 else None
        sol=sols.get(num,'')
        # Strip accidental page footer
        q=re.sub(r'Prepladder X Qbank.*?Page \d+ of 1310','',q,flags=re.S).strip()
        for o in opts:
            o['text']=re.sub(r'Prepladder X Qbank.*?Page \d+ of 1310','',o['text'],flags=re.S).strip()
        questions.append({'number':num,'question':q,'options':opts,'correct_answer':correct,'answer_index':ans_idx,'explanation':sol,'source_page':lesson['page']})
    return questions

def parse_pdf(path):
    doc=fitz.open(path)
    lessons=extract_toc(doc)
    # if TOC regex missed due to layout, use known page-title detection fallback
    results=[]
    for i,l in enumerate(lessons):
        next_page=lessons[i+1]['page'] if i+1<len(lessons) else None
        qs=parse_chapter(doc,l,next_page)
        results.append({'number':l['number'],'title':l['title'],'start_page':l['page'],'questions':qs})
    return {'subject':'Pediatrics','source_file':Path(path).name,'page_count':len(doc),'chapters':results}

if __name__=='__main__':
    import sys
    data=parse_pdf(sys.argv[1])
    json.dump(data,open(sys.argv[2],'w'),ensure_ascii=False,indent=2)
    print('chapters',len(data['chapters']),'questions',sum(len(x['questions']) for x in data['chapters']))
