import streamlit as st
from datetime import date
from supabase import create_client

st.set_page_config(page_title="말씀을 쓰다", page_icon="📖", layout="wide")

WRITERS=["가향","미자"]
BOOKS={
"구약":[("창세기",50),("출애굽기",40),("레위기",27),("민수기",36),("신명기",34),("여호수아",24),("사사기",21),("룻기",4),("사무엘상",31),("사무엘하",24),("열왕기상",22),("열왕기하",25),("역대상",29),("역대하",36),("에스라",10),("느헤미야",13),("에스더",10),("욥기",42),("시편",150),("잠언",31),("전도서",12),("아가",8),("이사야",66),("예레미야",52),("예레미야애가",5),("에스겔",48),("다니엘",12),("호세아",14),("요엘",3),("아모스",9),("오바댜",1),("요나",4),("미가",7),("나훔",3),("하박국",3),("스바냐",3),("학개",2),("스가랴",14),("말라기",4)],
"신약":[("마태복음",28),("마가복음",16),("누가복음",24),("요한복음",21),("사도행전",28),("로마서",16),("고린도전서",16),("고린도후서",13),("갈라디아서",6),("에베소서",6),("빌립보서",4),("골로새서",4),("데살로니가전서",5),("데살로니가후서",3),("디모데전서",6),("디모데후서",4),("디도서",3),("빌레몬서",1),("히브리서",13),("야고보서",5),("베드로전서",5),("베드로후서",3),("요한일서",5),("요한이서",1),("요한삼서",1),("유다서",1),("요한계시록",22)]}
BOOK_MAP={b:c for s in BOOKS.values() for b,c in s}; ALL=list(BOOK_MAP); TOTAL=sum(BOOK_MAP.values())

try:
    sb=create_client(st.secrets["SUPABASE_URL"],st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Supabase 연결 정보가 아직 설정되지 않았습니다. Streamlit Secrets에 SUPABASE_URL과 SUPABASE_KEY를 등록해 주세요.")
    st.stop()

def all_rows():
    return sb.table("bible_records").select("*").order("record_date",desc=True).order("id",desc=True).execute().data or []

rows=all_rows()
joint=len({(r["book"],r["chapter"]) for r in rows})
counts={w:sum(1 for r in rows if r["writer"]==w) for w in WRITERS}

st.markdown("""<style>
.stApp{background:linear-gradient(180deg,#f7f2e8,#fffdf9 52%,#f4efe5);color:#34372f}
.block-container{max-width:1120px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{color:#405044!important}
.hero{padding:2.2rem 2.4rem;border-radius:26px;background:#fffdf9;border:1px solid #dfd6c7;box-shadow:0 12px 34px rgba(80,67,46,.08);margin-bottom:1.3rem}
.hero small{letter-spacing:.14em;color:#777064;font-weight:700}.hero h1{font-size:2.5rem;margin:.3rem 0;color:#405044!important}.hero p{color:#6f695e}
[data-testid="stMetric"]{background:#fffdf9;border:1px solid #e2d8c8;padding:1rem;border-radius:18px}
[data-testid="stMetricLabel"] p{color:#69675e!important}[data-testid="stMetricValue"]{color:#405044!important}
[data-testid="stWidgetLabel"] p{color:#484b43!important;font-weight:700!important}
.stTextInput input,.stTextArea textarea,.stDateInput input{background:#fffdf9!important;color:#292b27!important;-webkit-text-fill-color:#292b27!important;border-radius:14px!important}
div[data-baseweb="select"]>div{background:#fffdf9!important;color:#292b27!important;border-radius:14px!important}
div[data-baseweb="select"] span{color:#292b27!important}
.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{background:#eee8dd;border-radius:14px;padding:0 20px;color:#55584e}.stTabs [aria-selected="true"]{background:#65725d!important}.stTabs [aria-selected="true"] p{color:white!important}
.stButton>button{border-radius:14px;background:#65725d;color:white;border:0;font-weight:700}.stButton>button p{color:white!important}
[data-testid="stProgress"]>div>div>div>div{background:#718069!important}
</style>""",unsafe_allow_html=True)

st.markdown("""<div class="hero"><small>OUR BIBLE TYPING JOURNAL</small><h1>📖 말씀을 쓰다</h1><p>가향과 미자가 함께 한 글자씩 쌓아가는 말씀 기록</p></div>""",unsafe_allow_html=True)
a,b,c,d=st.columns(4); a.metric("함께 기록한 장",f"{joint}장"); b.metric("가향의 기록",f"{counts['가향']}장"); c.metric("미자의 기록",f"{counts['미자']}장"); d.metric("전체 진행률",f"{joint/TOTAL*100:.1f}%"); st.progress(joint/TOTAL)

t1,t2,t3,t4=st.tabs(["✍️ 말씀 기록","🌿 함께 걷는 길","👤 개인 기록","🗂️ 지난 기록"])
with t1:
    w,dd=st.columns(2); writer=w.radio("작성자",WRITERS,horizontal=True); rd=dd.date_input("날짜",date.today())
    x,y=st.columns([2,1]); book=x.selectbox("성경",ALL); chapter=y.selectbox("장",range(1,BOOK_MAP[book]+1))
    old=next((r for r in rows if r["writer"]==writer and r["book"]==book and r["chapter"]==chapter),None)
    other=[r["writer"] for r in rows if r["writer"]!=writer and r["book"]==book and r["chapter"]==chapter]
    if other: st.info(f"💚 이 장은 {', '.join(set(other))}님도 기록했어요. 각자의 기록은 따로 저장됩니다.")
    if old: st.info(f"🌱 {writer}님의 기존 기록을 불러왔습니다. 수정 후 다시 저장할 수 있어요.")
    body=st.text_area("말씀 타이핑",old.get("body","") if old else "",height=360,placeholder="말씀을 한 글자씩 타이핑해 보세요...")
    p,q=st.columns(2); fav=p.text_input("💛 마음에 남은 말씀",old.get("favorite","") if old else ""); note=q.text_input("🌿 오늘의 한 줄",old.get("note","") if old else "")
    if st.button("오늘의 말씀 저장하기",type="primary",use_container_width=True):
        payload={"writer":writer,"record_date":rd.isoformat(),"book":book,"chapter":chapter,"body":body,"favorite":fav,"note":note}
        sb.table("bible_records").upsert(payload,on_conflict="writer,book,chapter").execute()
        st.success(f"✓ {writer} · {book} {chapter}장 저장 완료"); st.rerun()
with t2:
    st.subheader("함께 걷는 말씀 여정")
    for section,books in BOOKS.items():
        sec_done=sum(len({r["chapter"] for r in rows if r["book"]==bn}) for bn,_ in books); sec_total=sum(n for _,n in books)
        with st.expander(f"{'🌳' if section=='구약' else '🌱'} {section} · {sec_done}/{sec_total}장",expanded=(section=="구약")):
            for bn,total in books:
                n=len({r["chapter"] for r in rows if r["book"]==bn}); l,rcol=st.columns([2,5]); l.write(f"**{bn}** · {n}/{total}장"); rcol.progress(n/total)
with t3:
    person=st.radio("기록 보기",WRITERS,horizontal=True,key="pv"); mine=[r for r in rows if r["writer"]==person]
    st.metric(f"{person}님의 기록",f"{len(mine)}장"); st.progress(len(mine)/TOTAL)
    for r in mine:
        with st.expander(f"{r['record_date']} · {r['book']} {r['chapter']}장"):
            if r.get("favorite"): st.write("💛",r["favorite"])
            if r.get("note"): st.write("🌿",r["note"])
with t4:
    if not rows: st.info("아직 기록이 없어요.")
    for r in rows:
        with st.expander(f"{r['record_date']} · {r['writer']} · {r['book']} {r['chapter']}장"):
            if r.get("favorite"): st.markdown(f"**💛 마음에 남은 말씀**　{r['favorite']}")
            if r.get("note"): st.markdown(f"**🌿 오늘의 한 줄**　{r['note']}")
            if r.get("body"): st.text_area("말씀 기록",r["body"],height=180,disabled=True,key=f"b{r['id']}")
            if st.button("이 기록 삭제",key=f"d{r['id']}"):
                sb.table("bible_records").delete().eq("id",r["id"]).execute(); st.rerun()
