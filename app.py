import streamlit as st
from datetime import date
from supabase import create_client

st.set_page_config(page_title="말씀을 쓰다", page_icon="📖", layout="wide")

# 화면에는 영문 이름, DB에는 기존 한글 이름을 그대로 사용
DISPLAY_TO_DB = {"Gahyang": "가향", "Mija": "미자"}
DB_TO_DISPLAY = {v:k for k,v in DISPLAY_TO_DB.items()}

BOOKS = {
"구약":[("창세기",50),("출애굽기",40),("레위기",27),("민수기",36),("신명기",34),("여호수아",24),("사사기",21),("룻기",4),("사무엘상",31),("사무엘하",24),("열왕기상",22),("열왕기하",25),("역대상",29),("역대하",36),("에스라",10),("느헤미야",13),("에스더",10),("욥기",42),("시편",150),("잠언",31),("전도서",12),("아가",8),("이사야",66),("예레미야",52),("예레미야애가",5),("에스겔",48),("다니엘",12),("호세아",14),("요엘",3),("아모스",9),("오바댜",1),("요나",4),("미가",7),("나훔",3),("하박국",3),("스바냐",3),("학개",2),("스가랴",14),("말라기",4)],
"신약":[("마태복음",28),("마가복음",16),("누가복음",24),("요한복음",21),("사도행전",28),("로마서",16),("고린도전서",16),("고린도후서",13),("갈라디아서",6),("에베소서",6),("빌립보서",4),("골로새서",4),("데살로니가전서",5),("데살로니가후서",3),("디모데전서",6),("디모데후서",4),("디도서",3),("빌레몬서",1),("히브리서",13),("야고보서",5),("베드로전서",5),("베드로후서",3),("요한일서",5),("요한이서",1),("요한삼서",1),("유다서",1),("요한계시록",22)]
}
BOOK_MAP = {b:c for group in BOOKS.values() for b,c in group}
ALL_BOOKS = list(BOOK_MAP)
TOTAL = sum(BOOK_MAP.values())

try:
    sb = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception:
    st.error("Supabase 연결 정보가 없습니다. Streamlit Secrets를 확인해 주세요.")
    st.stop()

def get_rows():
    return sb.table("bible_records").select("*").order("record_date", desc=True).order("id", desc=True).execute().data or []

def is_complete(row):
    # 새 DB 컬럼 completed가 있으면 사용. 기존 기록은 기본적으로 완료 기록으로 간주.
    return bool(row.get("completed", True))

def refresh():
    st.rerun()

rows = get_rows()

# ---------- Design ----------
st.markdown("""
<style>
:root{--sage:#64735e;--sage2:#7d8d75;--cream:#faf7ef;--paper:#fffdf9;--ink:#343a33;--muted:#77766e;--line:#ded7ca;--soft:#eee9dd}
.stApp{background:linear-gradient(180deg,#f8f4eb 0%,#fffdf9 55%,#f5f1e8 100%);color:var(--ink)}
.block-container{max-width:1180px;padding-top:1.7rem;padding-bottom:4rem}
html,body,[class*="css"]{font-size:17px}
h1,h2,h3{color:#405044!important}
.hero{padding:2rem 2.25rem;border:1px solid var(--line);border-radius:25px;background:rgba(255,253,249,.94);box-shadow:0 10px 30px rgba(77,66,47,.07);margin-bottom:1.1rem}
.hero .eyebrow{font-size:.82rem;letter-spacing:.14em;color:#7d786d;font-weight:800}
.hero h1{font-size:2.55rem;margin:.25rem 0 .15rem!important}
.hero p{font-size:1.05rem;color:#696b63;margin:0}
[data-testid="stMetric"]{background:var(--paper);border:1px solid var(--line);padding:1.05rem 1.2rem;border-radius:18px;box-shadow:0 4px 16px rgba(70,60,45,.035)}
[data-testid="stMetricLabel"] p{color:#696b63!important;font-size:1rem!important;font-weight:700!important}
[data-testid="stMetricValue"]{color:#405044!important}
[data-testid="stProgress"]>div>div>div>div{background:var(--sage2)!important}

/* Tabs: generous padding, no red indicator */
.stTabs [data-baseweb="tab-list"]{gap:12px!important;border-bottom:0!important}
.stTabs [data-baseweb="tab"]{height:54px!important;padding:0 30px!important;background:var(--soft)!important;border-radius:14px!important;border:0!important;color:#4b5149!important}
.stTabs [data-baseweb="tab"] p,.stTabs [data-baseweb="tab"] span{color:#4b5149!important;font-size:1.03rem!important;font-weight:750!important;white-space:nowrap!important}
.stTabs [aria-selected="true"]{background:var(--sage)!important}
.stTabs [aria-selected="true"] p,.stTabs [aria-selected="true"] span{color:white!important}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none!important}

/* Labels / radio */
[data-testid="stWidgetLabel"] p,[data-testid="stRadio"] label p,[data-testid="stRadio"] label span{color:#40463e!important;opacity:1!important;font-size:1rem!important;font-weight:700!important}
[data-testid="stRadio"] [role="radiogroup"]{gap:1.6rem!important}

/* Inputs */
.stDateInput [data-baseweb="input"],.stTextInput [data-baseweb="input"],.stTextArea textarea,.stSelectbox [data-baseweb="select"]>div{
background:var(--paper)!important;color:#292d28!important;-webkit-text-fill-color:#292d28!important;border-color:#d5cec1!important;border-radius:13px!important}
.stDateInput input,.stTextInput input,.stSelectbox [data-baseweb="select"] *{color:#292d28!important;-webkit-text-fill-color:#292d28!important}
.stTextArea textarea{font-size:1.08rem!important;line-height:1.85!important;padding:18px!important}
.stTextArea textarea::placeholder,.stTextInput input::placeholder{color:#9b978e!important;-webkit-text-fill-color:#9b978e!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]{background:var(--paper)!important}
[role="option"],[role="option"] *{color:#292d28!important;background:var(--paper)!important}
[role="option"]:hover,[role="option"]:hover *{background:var(--soft)!important}

/* Buttons */
.stButton>button{min-height:48px;border-radius:13px!important;background:var(--sage)!important;color:white!important;border:0!important;font-weight:800!important;font-size:1rem!important}
.stButton>button p,.stButton>button span{color:white!important}
div[data-testid="stHorizontalBlock"] .stButton>button[kind="secondary"]{background:#87957f!important}

/* Cards / helpers */
.note{padding:1rem 1.1rem;background:#edf2e9;border:1px solid #d8e0d3;border-radius:14px;color:#4b5847;margin:.4rem 0 1rem}
.section-title{font-size:1.25rem;font-weight:850;color:#405044;margin:1rem 0 .25rem}
.small-muted{color:#7a786f;font-size:.94rem}
.status-draft{display:inline-block;padding:.18rem .55rem;border-radius:999px;background:#fff0d9;color:#a66a1c;font-weight:800;font-size:.82rem}
.status-done{display:inline-block;padding:.18rem .55rem;border-radius:999px;background:#e6f1e2;color:#52704d;font-weight:800;font-size:.82rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="eyebrow">OUR BIBLE TYPING JOURNAL</div>
 <h1>📖 말씀을 쓰다</h1>
 <p>한 장씩 서두르지 않고, 저장하고 이어 쓰는 우리의 말씀 기록</p>
</div>
""", unsafe_allow_html=True)

def writer_stats(db_name):
    mine=[r for r in rows if r.get("writer")==db_name]
    done=[r for r in mine if is_complete(r)]
    drafts=[r for r in mine if not is_complete(r)]
    return len(done), len(drafts)

g_done,g_draft=writer_stats("가향")
m_done,m_draft=writer_stats("미자")

c1,c2,c3=st.columns(3)
with c1:
    st.metric("🌿 Gahyang", f"{g_done}장", f"작성 중 {g_draft}장")
    st.progress(min(g_done/TOTAL,1.0))
    st.caption(f"완료 진행률 {g_done/TOTAL*100:.1f}% · {g_done:,}/{TOTAL:,}장")
with c2:
    st.metric("🌸 Mija", f"{m_done}장", f"작성 중 {m_draft}장")
    st.progress(min(m_done/TOTAL,1.0))
    st.caption(f"완료 진행률 {m_done/TOTAL*100:.1f}% · {m_done:,}/{TOTAL:,}장")
with c3:
    st.metric("📖 전체 성경", f"{TOTAL:,}장")
    st.caption("구약 929장 · 신약 260장")

tab_write,tab_progress,tab_history=st.tabs(["✍️ 말씀 기록","📊 나의 진행","🗂️ 지난 기록"])

with tab_write:
    st.markdown('<div class="section-title">1. 기록할 내용을 선택하세요</div>',unsafe_allow_html=True)
    a,b,c,d=st.columns([1.1,1,1,1])
    display_writer=a.selectbox("작성자",["Gahyang","Mija"])
    db_writer=DISPLAY_TO_DB[display_writer]
    record_date=b.date_input("날짜",date.today())
    book=c.selectbox("성경",ALL_BOOKS)
    chapter=d.selectbox("장",range(1,BOOK_MAP[book]+1))

    old=next((r for r in rows if r.get("writer")==db_writer and r.get("book")==book and int(r.get("chapter",0))==chapter),None)
    if old:
        status="완료" if is_complete(old) else "작성 중"
        st.markdown(f'<div class="note">💡 {display_writer}님의 <b>{book} {chapter}장</b> 기존 기록을 불러왔습니다. 현재 상태: <b>{status}</b><br>저장된 내용 아래에서 그대로 이어서 작성하세요.</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="note">💡 한 장을 한 번에 모두 작성하지 않아도 됩니다. <b>임시 저장</b> 후 다음에 같은 작성자·성경·장을 선택하면 자동으로 이어서 작성할 수 있습니다.</div>',unsafe_allow_html=True)

    st.markdown('<div class="section-title">2. 성경 본문을 타이핑하세요</div>',unsafe_allow_html=True)
    body=st.text_area("말씀 타이핑",value=old.get("body","") if old else "",height=430,placeholder="말씀을 한 글자씩 천천히 타이핑해 보세요...")

    st.markdown('<div class="section-title">3. 오늘의 말씀 기록</div>',unsafe_allow_html=True)
    # 기존 favorite/note가 있으면 잃지 않도록 합쳐 보여줌
    reflection=""
    if old:
        reflection=(old.get("note") or "").strip()
        fav=(old.get("favorite") or "").strip()
        if not reflection and fav: reflection=fav
        elif fav and fav not in reflection: reflection=f"{fav}\n{reflection}".strip()
    reflection=st.text_area("마음에 남은 구절이나 생각",value=reflection,height=125,placeholder="타이핑하며 마음에 남은 구절이나 생각을 자유롭게 남겨보세요.")

    st.markdown('<div class="section-title">4. 저장하기</div>',unsafe_allow_html=True)
    save_col,done_col=st.columns(2)
    if save_col.button("💾 임시 저장",use_container_width=True):
        payload={"writer":db_writer,"record_date":record_date.isoformat(),"book":book,"chapter":chapter,"body":body,"favorite":"","note":reflection,"completed":False}
        sb.table("bible_records").upsert(payload,on_conflict="writer,book,chapter").execute()
        st.success(f"{display_writer} · {book} {chapter}장 작성 내용을 저장했습니다. 다음에 이어서 작성할 수 있어요.")
        refresh()
    if done_col.button("✓ 이 장 완료",use_container_width=True,type="primary"):
        if not body.strip():
            st.warning("완료하기 전에 말씀 본문을 입력해 주세요.")
        else:
            payload={"writer":db_writer,"record_date":record_date.isoformat(),"book":book,"chapter":chapter,"body":body,"favorite":"","note":reflection,"completed":True}
            sb.table("bible_records").upsert(payload,on_conflict="writer,book,chapter").execute()
            st.success(f"✓ {display_writer} · {book} {chapter}장을 완료했습니다.")
            refresh()

with tab_progress:
    st.markdown('<div class="section-title">나의 진행 현황</div>',unsafe_allow_html=True)
    person=st.radio("작성자 선택",["Gahyang","Mija"],horizontal=True,key="progress_writer")
    dbp=DISPLAY_TO_DB[person]
    mine=[r for r in rows if r.get("writer")==dbp]
    done=[r for r in mine if is_complete(r)]
    drafts=[r for r in mine if not is_complete(r)]
    x,y,z=st.columns(3)
    x.metric("완료",f"{len(done)}장")
    y.metric("작성 중",f"{len(drafts)}장")
    z.metric("진행률",f"{len(done)/TOTAL*100:.1f}%")
    st.progress(min(len(done)/TOTAL,1.0))

    if drafts:
        st.markdown('<div class="section-title">✏️ 작성 중인 장</div>',unsafe_allow_html=True)
        for r in drafts:
            st.write(f"• {r['book']} {r['chapter']}장 · 마지막 저장 {r['record_date']}")
    st.markdown('<div class="section-title">성경별 완료 현황</div>',unsafe_allow_html=True)
    for section,books in BOOKS.items():
        sec_done=sum(1 for r in done if r.get("book") in [b for b,_ in books])
        sec_total=sum(n for _,n in books)
        with st.expander(f"{'🌳' if section=='구약' else '🌱'} {section} · {sec_done}/{sec_total}장",expanded=(section=="구약")):
            for bn,total in books:
                n=sum(1 for r in done if r.get("book")==bn)
                left,right=st.columns([2,5])
                left.write(f"**{bn}** · {n}/{total}장")
                right.progress(min(n/total,1.0))

with tab_history:
    st.markdown('<div class="section-title">지난 기록</div>',unsafe_allow_html=True)
    f1,f2,f3=st.columns(3)
    who=f1.selectbox("작성자",["전체","Gahyang","Mija"],key="hist_writer")
    book_filter=f2.selectbox("성경",["전체"]+ALL_BOOKS,key="hist_book")
    status_filter=f3.selectbox("상태",["전체","작성 중","완료"],key="hist_status")

    filtered=rows[:]
    if who!="전체": filtered=[r for r in filtered if r.get("writer")==DISPLAY_TO_DB[who]]
    if book_filter!="전체": filtered=[r for r in filtered if r.get("book")==book_filter]
    if status_filter=="작성 중": filtered=[r for r in filtered if not is_complete(r)]
    elif status_filter=="완료": filtered=[r for r in filtered if is_complete(r)]

    if not filtered:
        st.info("조건에 맞는 기록이 없습니다.")
    for r in filtered:
        disp=DB_TO_DISPLAY.get(r.get("writer"),r.get("writer",""))
        stat="완료" if is_complete(r) else "작성 중"
        icon="✅" if is_complete(r) else "📝"
        with st.expander(f"{icon} {r['record_date']} · {disp} · {r['book']} {r['chapter']}장 · {stat}"):
            if r.get("note"):
                st.markdown("**🌿 오늘의 말씀 기록**")
                st.write(r["note"])
            if r.get("body"):
                st.text_area("말씀 기록",r["body"],height=220,disabled=True,key=f"body_{r['id']}")
            if st.button("🗑️ 이 기록 삭제",key=f"delete_{r['id']}"):
                sb.table("bible_records").delete().eq("id",r["id"]).execute()
                refresh()
