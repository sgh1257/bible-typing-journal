import streamlit as st
from datetime import date
import re
from streamlit_quill import st_quill
import streamlit.components.v1 as components
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


# ---------- helpers ----------
def parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return date.today()

def find_record_by_id(record_id):
    if record_id is None:
        return None
    return next((r for r in rows if str(r.get("id")) == str(record_id)), None)

def save_record(existing, payload):
    """기존 기록은 id로 update, 새 기록은 insert.
    실패 시 예외를 그대로 올려 화면에서 원인을 확인할 수 있게 함.
    """
    if existing and existing.get("id") is not None:
        return sb.table("bible_records").update(payload).eq("id", existing["id"]).execute()
    return sb.table("bible_records").insert(payload).execute()

def open_record(record_id):
    st.session_state["edit_record_id"] = record_id
    st.session_state["main_menu"] = "✍️ 말씀 기록"

def new_record():
    st.session_state.pop("edit_record_id", None)
    st.session_state["main_menu"] = "✍️ 말씀 기록"
    st.session_state["active_writer"] = "Gahyang"

def set_menu(menu_name):
    st.session_state["main_menu"] = menu_name

def set_writer(writer_name):
    st.session_state["active_writer"] = writer_name

def plain_to_quill_html(body):
    """기존 일반 텍스트를 실시간 절 번호 편집기의 번호 목록으로 변환."""
    if not body or not body.strip():
        return "<ol><li><br></li></ol>"
    lines=[ln.strip() for ln in body.splitlines() if ln.strip()]
    items=[]
    for ln in lines:
        ln=re.sub(r"^\s*\d+\s*(?:절|[.)])?\s*", "", ln)
        safe=ln.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        items.append(f"<li>{safe}</li>")
    return "<ol>"+"".join(items)+"</ol>"

def quill_to_plain(html):
    """편집기 내용을 DB 저장용 일반 텍스트로 변환."""
    if not html:
        return ""
    items=re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S|re.I)
    if items:
        out=[]
        for i,item in enumerate(items,1):
            item=re.sub(r"<br\s*/?>", "\n", item, flags=re.I)
            item=re.sub(r"<[^>]+>", "", item)
            item=(item.replace("&nbsp;"," ").replace("&amp;","&")
                      .replace("&lt;","<").replace("&gt;",">")).strip()
            if item:
                out.append(f"{i}  {item}")
        return "\n".join(out)
    text=re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text=re.sub(r"<[^>]+>", "", text)
    return text.strip()

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

/* 상단 메뉴와 작성자 카드는 Streamlit 버튼 자체를 사용 */
.nav-wrap{margin:.65rem 0 1.2rem}
.writer-label{font-size:1rem;font-weight:800;color:#40463e;margin:.35rem 0 .45rem}
.writer-selected{
    padding:14px 18px;border:2px solid #64735e;border-radius:16px;background:#edf2e9;
    min-height:72px;box-shadow:0 4px 14px rgba(75,95,70,.10)
}
.writer-selected .name{font-size:1.13rem;font-weight:900;color:#344136}
.writer-selected .sub{font-size:.86rem;color:#687264;margin-top:2px}
.writer-unselected{
    padding:14px 18px;border:1px solid #d7d2c6;border-radius:16px;background:#fffdf9;
    min-height:72px
}
.writer-unselected .name{font-size:1.13rem;font-weight:850;color:#4c514b}
.writer-unselected .sub{font-size:.86rem;color:#8a887f;margin-top:2px}
[data-testid="stWidgetLabel"] p{color:#40463e!important;opacity:1!important;font-size:1rem!important;font-weight:750!important}

/* 말씀 필사 편집기 */
div[data-testid="stCustomComponentV1"] iframe{min-height:470px!important}
.verse-heading{
    background:#f4f0e6;border:1px solid #ded7ca;border-bottom:0;
    border-radius:16px 16px 0 0;padding:14px 18px 12px;margin-top:.55rem
}
.verse-heading .book{font-size:1.15rem;font-weight:900;color:#405044}
.verse-heading .guide{font-size:.9rem;color:#77766e;margin-top:3px}

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
.note{padding:1rem 1.1rem;background:#edf2e9;border:1px solid #d8e0d3;border-radius:14px;color:#4b5847;margin:.4rem 0 1rem}
.section-title{font-size:1.25rem;font-weight:850;color:#405044;margin:1rem 0 .25rem}
.small-muted{color:#7a786f;font-size:.94rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="eyebrow">OUR BIBLE TYPING JOURNAL</div>
 <h1>📖 말씀을 쓰다</h1>
 <p>한 장씩 서두르지 않고, 저장하고 이어 쓰는 우리의 말씀 기록</p>
</div>
""", unsafe_allow_html=True)

def chapter_key(row):
    """같은 작성자·성경·장을 하나의 장으로 계산하기 위한 키."""
    try:
        chapter = int(row.get("chapter"))
    except (TypeError, ValueError):
        chapter = row.get("chapter")
    return (row.get("book"), chapter)

def unique_chapters(records):
    """동일 성경/장이 여러 번 저장되어도 진행률에서는 한 장으로 계산."""
    return {chapter_key(r) for r in records if r.get("book") and r.get("chapter") is not None}

def writer_stats(db_name):
    mine=[r for r in rows if r.get("writer")==db_name]
    done=[r for r in mine if is_complete(r)]
    drafts=[r for r in mine if not is_complete(r)]
    done_keys=unique_chapters(done)
    # 이미 완료된 장의 임시 저장본은 '작성 중'에서 제외
    draft_keys=unique_chapters(drafts) - done_keys
    return len(done_keys), len(draft_keys)

g_done,g_draft=writer_stats("가향")
m_done,m_draft=writer_stats("미자")

c1,c2,c3=st.columns(3)
with c1:
    st.metric("🌿 Gahyang", f"{g_done}장")
    st.progress(min(g_done/TOTAL,1.0))
    st.caption(f"완료 진행률 {g_done/TOTAL*100:.1f}% · {g_done:,}/{TOTAL:,}장" + (f" · 작성 중 {g_draft}장" if g_draft else ""))
with c2:
    st.metric("🌸 Mija", f"{m_done}장")
    st.progress(min(m_done/TOTAL,1.0))
    st.caption(f"완료 진행률 {m_done/TOTAL*100:.1f}% · {m_done:,}/{TOTAL:,}장" + (f" · 작성 중 {m_draft}장" if m_draft else ""))
with c3:
    st.metric("📖 전체 성경", f"{TOTAL:,}장")
    st.caption("구약 929장 · 신약 260장")

if "main_menu" not in st.session_state:
    st.session_state["main_menu"] = "✍️ 말씀 기록"
if "active_writer" not in st.session_state:
    st.session_state["active_writer"] = "Gahyang"

menu_names=["✍️ 말씀 기록","📊 나의 진행","🗂️ 지난 기록"]
nav1,nav2,nav3=st.columns(3)
for col,name in zip([nav1,nav2,nav3],menu_names):
    selected = st.session_state["main_menu"] == name
    label = ("● " if selected else "") + name
    col.button(
        label,
        key=f"nav_{name}",
        use_container_width=True,
        type="primary" if selected else "secondary",
        on_click=set_menu,
        args=(name,)
    )
menu=st.session_state["main_menu"]

if menu == "✍️ 말씀 기록":
    # 과거 기록은 '지난 기록 > 기록 열기'로 들어왔을 때만 불러옴
    editing = find_record_by_id(st.session_state.get("edit_record_id"))

    top_l, top_r = st.columns([5,1])
    with top_l:
        st.markdown('<div class="section-title">1. 기록할 내용을 선택하세요</div>',unsafe_allow_html=True)
    with top_r:
        if editing:
            st.button("＋ 새 기록", use_container_width=True, on_click=new_record)

    default_display = DB_TO_DISPLAY.get(editing.get("writer"), "Gahyang") if editing else st.session_state.get("active_writer","Gahyang")
    if editing:
        st.session_state["active_writer"] = default_display

    st.markdown('<div class="writer-label">작성자</div>',unsafe_allow_html=True)
    wc1,wc2=st.columns(2)
    for col,w,icon,kr in [
        (wc1,"Gahyang","🌿","가향"),
        (wc2,"Mija","🌸","미자")
    ]:
        selected = st.session_state.get("active_writer","Gahyang") == w
        box_class="writer-selected" if selected else "writer-unselected"
        mark=" · 선택됨" if selected else ""
        col.markdown(
            f'<div class="{box_class}"><div class="name">{icon} {w}</div>'
            f'<div class="sub">{kr}{mark}</div></div>',
            unsafe_allow_html=True
        )
        if col.button(
            f"{'✓ ' if selected else ''}{w} 선택",
            key=f"writer_btn_{w}_{editing.get('id') if editing else 'new'}",
            use_container_width=True,
            type="primary" if selected else "secondary",
            disabled=selected,
            on_click=set_writer,
            args=(w,)
        ):
            pass

    display_writer=st.session_state.get("active_writer","Gahyang")
    db_writer=DISPLAY_TO_DB[display_writer]

    default_book = editing.get("book") if editing and editing.get("book") in ALL_BOOKS else ALL_BOOKS[0]
    default_chapter = int(editing.get("chapter",1)) if editing else 1

    b,c,d=st.columns([1,1.4,.7])
    record_date=b.date_input(
        "날짜",
        parse_date(editing.get("record_date")) if editing else date.today(),
        key=f"record_date_{editing.get('id') if editing else 'new'}"
    )
    book=c.selectbox(
        "성경",
        ALL_BOOKS,
        index=ALL_BOOKS.index(default_book),
        key=f"book_{editing.get('id') if editing else 'new'}"
    )
    chapter_options=list(range(1,BOOK_MAP[book]+1))
    chapter=d.selectbox(
        "장",
        chapter_options,
        index=chapter_options.index(default_chapter) if default_chapter in chapter_options else 0,
        key=f"chapter_{editing.get('id') if editing else 'new'}"
    )

    if editing:
        status="완료" if is_complete(editing) else "작성 중"
        st.markdown(
            f'<div class="note">📖 <b>{editing["record_date"]}</b>에 저장한 '
            f'<b>{DB_TO_DISPLAY.get(editing.get("writer"), editing.get("writer",""))} · '
            f'{editing.get("book")} {editing.get("chapter")}장</b> 기록을 열었습니다. '
            f'현재 상태: <b>{status}</b><br>수정 후 아래 저장 버튼을 누르면 이 기록이 업데이트됩니다.</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="note">🌿 오늘의 새 기록입니다. 과거 기록은 자동으로 불러오지 않습니다. '
            '이전에 저장한 내용을 이어 쓰려면 <b>지난 기록 → 기록 열기</b>를 이용하세요.</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title">2. 성경 본문을 타이핑하세요</div>',unsafe_allow_html=True)
    st.markdown(
        f'<div class="verse-heading"><div class="book">📖 {book} {chapter}장</div>'
        '<div class="guide">말씀을 한 절씩 천천히 기록해 보세요.</div></div>',
        unsafe_allow_html=True
    )
    initial_body=editing.get("body","") if editing else ""
    editor_html=st_quill(
        value=plain_to_quill_html(initial_body),
        html=True,
        toolbar=[],
        placeholder="1절 말씀을 입력하세요.",
        key=f"verse_editor_{editing.get('id') if editing else 'new'}"
    )
    body=quill_to_plain(editor_html)

    # 브라우저 맞춤법 검사 해제 + 편집기 글씨/절 간격 조정
    components.html("""
    <script>
    function tuneEditor(){
      try{
        const frames = window.parent.document.querySelectorAll('iframe');
        frames.forEach((frame)=>{
          try{
            const doc = frame.contentDocument || frame.contentWindow.document;
            if(!doc) return;
            const editor = doc.querySelector('.ql-editor');
            if(editor){
              editor.setAttribute('spellcheck','false');
              editor.setAttribute('autocorrect','off');
              editor.setAttribute('autocapitalize','off');
              editor.style.fontSize='18px';
              editor.style.lineHeight='1.75';
              editor.style.minHeight='390px';
              const lis=editor.querySelectorAll('li');
              lis.forEach(li=>{
                li.style.marginBottom='13px';
                li.style.paddingLeft='6px';
              });
            }
            const toolbar=doc.querySelector('.ql-toolbar');
            if(toolbar) toolbar.style.display='none';
            const container=doc.querySelector('.ql-container');
            if(container){
              container.style.borderTop='1px solid #ded7ca';
              container.style.fontFamily='inherit';
            }
          }catch(e){}
        });
      }catch(e){}
    }
    setTimeout(tuneEditor,250);
    setTimeout(tuneEditor,800);
    setTimeout(tuneEditor,1600);
    </script>
    """, height=0)
    st.caption("Enter를 누르는 즉시 다음 절 번호가 1 → 2 → 3…으로 나타납니다. 자동 줄바꿈은 같은 절로 유지됩니다.")

    st.markdown('<div class="section-title">3. 오늘의 말씀 기록</div>',unsafe_allow_html=True)
    reflection=""
    if editing:
        reflection=(editing.get("note") or "").strip()
        fav=(editing.get("favorite") or "").strip()
        if not reflection and fav: reflection=fav
        elif fav and fav not in reflection: reflection=f"{fav}\n{reflection}".strip()
    reflection=st.text_area(
        "마음에 남은 구절이나 생각",
        value=reflection,
        height=125,
        placeholder="타이핑하며 마음에 남은 구절이나 생각을 자유롭게 남겨보세요.",
        key=f"reflection_{editing.get('id') if editing else 'new'}"
    )

    st.markdown('<div class="section-title">4. 저장하기</div>',unsafe_allow_html=True)
    save_col,done_col=st.columns(2)

    if save_col.button("💾 임시 저장",use_container_width=True):
        payload={
            "writer":db_writer,"record_date":record_date.isoformat(),"book":book,
            "chapter":chapter,"body":body,"favorite":"",
            "note":reflection,"completed":False
        }
        try:
            save_record(editing,payload)
            st.success(f"💾 {display_writer} · {book} {chapter}장 내용을 임시 저장했습니다.")
            st.session_state.pop("edit_record_id", None)
            refresh()
        except Exception as e:
            st.error("저장에 실패했습니다. 아래 오류 내용을 확인해 주세요.")
            st.code(str(e))

    if done_col.button("✓ 이 장 완료",use_container_width=True,type="primary"):
        if not body.strip():
            st.warning("완료하기 전에 말씀 본문을 입력해 주세요.")
        else:
            payload={
                "writer":db_writer,"record_date":record_date.isoformat(),"book":book,
                "chapter":chapter,"body":body,"favorite":"",
                "note":reflection,"completed":True
            }
            try:
                save_record(editing,payload)
                st.success(f"✓ {display_writer} · {book} {chapter}장을 완료했습니다.")
                st.session_state.pop("edit_record_id", None)
                refresh()
            except Exception as e:
                st.error("저장에 실패했습니다. 아래 오류 내용을 확인해 주세요.")
                st.code(str(e))

elif menu == "📊 나의 진행":
    st.markdown('<div class="section-title">나의 진행 현황</div>',unsafe_allow_html=True)
    st.markdown("**작성자 선택**")
    pc1,pc2=st.columns(2)
    current_progress=st.session_state.get("progress_writer","Gahyang")
    if pc1.button(("✓ " if current_progress=="Gahyang" else "")+"🌿 Gahyang",key="progress_g",use_container_width=True,type="primary" if current_progress=="Gahyang" else "secondary"):
        st.session_state["progress_writer"]="Gahyang"; st.rerun()
    if pc2.button(("✓ " if current_progress=="Mija" else "")+"🌸 Mija",key="progress_m",use_container_width=True,type="primary" if current_progress=="Mija" else "secondary"):
        st.session_state["progress_writer"]="Mija"; st.rerun()
    person=st.session_state.get("progress_writer","Gahyang")
    dbp=DISPLAY_TO_DB[person]
    mine=[r for r in rows if r.get("writer")==dbp]
    done=[r for r in mine if is_complete(r)]
    drafts=[r for r in mine if not is_complete(r)]
    done_keys=unique_chapters(done)
    draft_keys=unique_chapters(drafts) - done_keys
    done_count=len(done_keys)
    draft_count=len(draft_keys)

    x,y,z=st.columns(3)
    x.metric("완료",f"{done_count}장")
    y.metric("작성 중",f"{draft_count}장")
    z.metric("진행률",f"{done_count/TOTAL*100:.1f}%")
    st.progress(min(done_count/TOTAL,1.0))

    if draft_keys:
        st.markdown('<div class="section-title">✏️ 작성 중인 장</div>',unsafe_allow_html=True)
        shown=set()
        for r in drafts:
            key=chapter_key(r)
            if key in draft_keys and key not in shown:
                st.write(f"• {r['book']} {r['chapter']}장 · 마지막 저장 {r['record_date']}")
                shown.add(key)

    st.markdown('<div class="section-title">성경별 완료 현황</div>',unsafe_allow_html=True)
    for section,books in BOOKS.items():
        section_names={b for b,_ in books}
        sec_done=sum(1 for book,chapter in done_keys if book in section_names)
        sec_total=sum(n for _,n in books)
        with st.expander(f"{'🌳' if section=='구약' else '🌱'} {section} · {sec_done}/{sec_total}장",expanded=(section=="구약")):
            for bn,total in books:
                n=sum(1 for book,chapter in done_keys if book==bn)
                left,right=st.columns([2,5])
                left.write(f"**{bn}** · {n}/{total}장")
                right.progress(min(n/total,1.0))

elif menu == "🗂️ 지난 기록":
    st.markdown('<div class="section-title">지난 기록</div>',unsafe_allow_html=True)
    st.caption("Gahyang과 Mija의 전체 기록입니다. 작성자·성경·상태별로 골라 볼 수 있으며, 이어 쓰거나 수정할 때는 ‘기록 열기’를 눌러 주세요.")
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
                st.text_area("말씀 기록",r["body"],height=220,disabled=True,key=f"hist_body_{r['id']}")
            oc,dc=st.columns([2,1])
            oc.button(
                "✍️ 기록 열기",
                key=f"open_{r['id']}",
                use_container_width=True,
                on_click=open_record,
                args=(r["id"],)
            )
            if dc.button("🗑️ 삭제",key=f"delete_{r['id']}",use_container_width=True):
                try:
                    sb.table("bible_records").delete().eq("id",r["id"]).execute()
                    st.success("기록을 삭제했습니다.")
                    refresh()
                except Exception as e:
                    st.error("삭제에 실패했습니다.")
                    st.code(str(e))
