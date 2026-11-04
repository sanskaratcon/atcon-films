"""Builds the v11 case study pages: one page per case, in the home page's own design.

The words come from ATCON's case study library (the Deck of 27 July, rewritten in plain language): who it is for,
the challenge, what we built, the highlights, the outcomes and the two headline figures. Client names are never
used; each story is told by its sector. Each page shows the case's own illustration, taken from its card on the home
page, and the buttons are the home page's own (their styles are copied from it), so the pages always match it.

Run from the repository root:  python tools/build_case_pages.py
It writes public/v11/cases/<slug>.html and public/v11/cases/case.css, and turns each case card's "View case study"
on the home page into a link to its page (safe to run again).
"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V11 = os.path.join(ROOT, 'public', 'v11')
OUT = os.path.join(V11, 'cases')

# in the order the cards come on the home page
CASES = [
    dict(slug='linkedin-lead-generation-agent', sector='B2B sales', tag='Automation',
         one_liner='AI-driven LinkedIn prospecting that keeps a steady pipeline of qualified B2B leads.',
         for_whom='B2B sales teams that lose time on manual prospecting and inconsistent outreach.',
         problem='Manual prospecting and inconsistent LinkedIn outreach took too much time and produced too few leads.',
         built='An AI agent that finds prospects, personalizes outreach, runs follow-up sequences and alerts the sales team when a prospect shows buying intent.',
         highlights=['AI-powered prospect discovery', 'Personalized outreach at scale', 'Automated follow-up sequences', 'CRM synchronization'],
         outcomes=['Manual outreach replaced by scalable AI-assisted lead generation', 'More engagement through consistent, personalized outreach',
                   'Automated follow-ups that reduce missed opportunities', 'A steady pipeline of qualified B2B leads', 'Sales time spent on high-value conversations'],
         stats=[('24/7', 'Active pipeline'), ('AI', 'Powered agent')]),
    dict(slug='b2b-valuation-platform-strategy', sector='Real estate technology', tag='Platform strategy',
         one_liner='A platform strategy to embed property valuation tools into partner ecosystems.',
         for_whom='Product companies that want to offer their solution through partners as an embeddable B2B product.',
         problem='A Belgian real estate technology company needed a scalable strategy to launch its property valuation solution as an embeddable B2B product.',
         built='Product advisory, the integration approach, stakeholder alignment and a structured delivery roadmap that made partner adoption straightforward.',
         highlights=['Embeddable B2B product model', 'Freemium access strategy', 'Integration-first thinking', 'Execution clarity and alignment'],
         outcomes=['A clear embeddable product model for partners', 'A freemium access strategy agreed with stakeholders',
                   'An integration-first roadmap the team could execute'],
         stats=[('01', 'Platform strategy'), ('B2B', 'Partner ecosystem')]),
    dict(slug='financial-automation-ecosystem', sector='Accounting and advisory', tag='Automation',
         one_liner='Automated financial workflows that produce reports, insights and client-ready updates.',
         for_whom='Accounting and advisory firms that spend their time on manual reporting and client communication.',
         problem='Reporting, client communication and financial documentation were manual, which limited efficiency and left data unused.',
         built='An AI-powered automation platform that generates presentation-ready reports, gives advisors an intelligent financial assistant, and creates client-ready newsletters from financial and regulatory updates.',
         highlights=['Context-aware AI assistant', 'Intelligent automation layer', 'Connected data integration'],
         outcomes=['Accounting operations turned into a scalable, insight-led advisory practice', 'Report generation time cut by more than 70 percent',
                   'Faster, clearer and more proactive client communication', 'Instant financial insights inside daily workflows',
                   'Teams shifted to higher-value guidance with data compliance kept'],
         stats=[('70%+', 'Report time reduced'), ('GDPR', 'Compliant')]),
    dict(slug='healthcare-voice-agent', sector='Healthcare', tag='Automation',
         one_liner='A 24/7 AI voice assistant that answers patient calls and books appointments.',
         for_whom='Clinics, hospital groups and practices with high call volumes and a busy front desk.',
         problem='High call volumes and limited administrative capacity led to missed patient calls and missed appointments.',
         built='An AI voice agent that handles patient calls, schedules and moves appointments, updates the CRM and manages bookings in real time.',
         highlights=['24/7 AI voice agent', 'Automated appointment management', 'Structured data collection', 'Workflow and CRM synchronization'],
         outcomes=['Less administrative work through automated calls and scheduling', 'Staff freed from repetitive tasks to focus on patient care',
                   'Every patient call answered at once, whatever the volume', 'Faster and more accurate appointment management',
                   'Calls, appointments and requests in one system'],
         stats=[('24/7', 'Always available'), ('00', 'Missed calls')]),
    dict(slug='retail-distribution-digitization', sector='Consumer brands and retail', tag='Digital transformation',
         one_liner='A central mobile platform for real-time sales tracking, schemes and channel operations.',
         for_whom='Consumer brands with retailers, distributors and field sales teams.',
         problem='Retail and distribution operations ran on manual reporting, which meant limited visibility, delayed payouts and inefficient channel management.',
         built='A central, role-based mobile app that digitized sales, schemes and incentive tracking, with real-time analytics, reward redemption and dashboards for every channel stakeholder.',
         highlights=['Role-based dashboards', 'Real-time analytics', 'Instant redemption', 'Unified platform'],
         outcomes=['Manual Excel processes removed across retail and distribution', 'Real-time visibility into sales, schemes and incentives',
                   'Faster payouts and reward redemption across the channel', 'More transparency between retailers, distributors and sales teams',
                   'A scalable digital platform the brand can build on'],
         stats=[('01', 'Unified platform'), ('04', 'Stakeholder roles')]),
    dict(slug='manufacturing-sales-production-automation', sector='Manufacturing', tag='Automation',
         one_liner='One CRM that connects lead capture, the sales pipeline and production jobs.',
         for_whom='Manufacturers that run leads, sales and order processing in disconnected tools.',
         problem='Leads, sales and order processing lived in separate tools, which caused delays and limited visibility.',
         built='A custom CRM that centralizes lead capture, automates follow-ups and sales workflows, and turns confirmed orders into production jobs in one platform.',
         highlights=['Automated lead capture', 'End-to-end CRM workflow', 'Sales and production sync'],
         outcomes=['Full visibility of the sales funnel, follow-ups and conversions', 'Fewer manual handoffs between sales and production',
                   'Faster response times and better pipeline management', 'More efficient sales and manufacturing teams', 'A CRM that scales with the business'],
         stats=[('01', 'Unified platform'), ('03+', 'Lead sources')]),
]

LOGO = ('<svg viewBox="0 8 506 490" fill="currentColor" aria-hidden="true"><path d="M215 11H304L92 494H0Z"></path>'
        '<path d="M365 173L506 493H417L320 272Z"></path></svg>')
ARROW = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M2 6h8M6.5 2.5L10 6l-3.5 3.5"></path></svg>'
BACK = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M10 6H2M5.5 2.5L2 6l3.5 3.5"></path></svg>'
CHECK = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8.4l2.6 2.6L12 5.4"></path></svg>'

index_path = os.path.join(V11, 'index.html')
page = open(index_path, encoding='utf-8').read()
cards = list(re.finditer(r'<article class="csf-card">(.*?)</article>', page, re.S))
assert len(cards) == len(CASES), 'expected %d case cards' % len(CASES)
for c, m in zip(CASES, cards):
    c['title'] = html.unescape(re.search(r'<h3>(.*?)</h3>', m.group(1)).group(1))
    c['art'] = re.search(r'<svg class="il-svg".*?</svg>', m.group(1), re.S).group(0)

# the home page's own buttons, copied so the pages always match it
btn = page[page.index('/* buttons as the site\'s own surfaces'):page.index('.atc[data-menu="open"] .atc-chrome')]


def figure(v):
    """the figure in navy, any trailing sign (%, +) in the brand gradient, as on the home page's results"""
    m = re.match(r'^(.*?\d)([%+]+)$', v)
    if m:
        return '%s<span class="cp-unit">%s</span>' % (html.escape(m.group(1)), html.escape(m.group(2)))
    return html.escape(v)


CSS = '''/* Case study pages: the home page's own type, colours, cards and buttons, on white. Built by
   tools/build_case_pages.py - edit there, not here. */
html{scroll-behavior:smooth}
body{margin:0;background:#FFFFFF;color:var(--atc-navy);font-family:var(--atc-font);-webkit-font-smoothing:antialiased}
*{box-sizing:border-box}
a{color:inherit}
.cp-in{width:100%;max-width:1320px;margin:0 auto;padding:0 clamp(20px,5vw,72px)}
.cp-label{margin:0 0 var(--sp-5)}
.cp-muted{color:var(--atc-slate)}

/* the header: the mark, the way back, and Contact */
.cp-head{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.92);border-bottom:1px solid rgba(0,16,37,.08)}
.cp-head .cp-in{display:flex;align-items:center;gap:var(--sp-6);height:72px}
.cp-logo{display:flex;color:var(--atc-navy)}
.cp-logo svg{width:22px;height:auto;display:block}
.cp-back{display:inline-flex;align-items:center;gap:10px;margin-right:auto;font-size:14px;font-weight:500;color:var(--atc-slate);text-decoration:none;transition:color .25s ease}
.cp-back svg{width:12px;height:12px;transition:transform .3s cubic-bezier(.2,.8,.3,1)}
.cp-back:hover{color:var(--atc-navy)}
.cp-back:hover svg{transform:translateX(-3px)}

/* the opening: the case's number and focus, its title and summary, its sector, and its own scene */
.cp-hero{padding:clamp(48px,9vh,112px) 0 clamp(32px,5vh,64px)}
.cp-hero .cp-in{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);gap:clamp(32px,5vw,88px);align-items:center}
.cp-hero h1{margin:0;text-wrap:balance}
.cp-hero .ds-lede{margin:var(--sp-5) 0 0;max-width:30em;color:var(--atc-slate)}
.cp-facts{display:grid;grid-template-columns:repeat(2,minmax(0,auto));justify-content:start;gap:var(--sp-7);margin:var(--sp-7) 0 0;padding-top:var(--sp-5);border-top:1px solid #E7ECF5}
.cp-facts dt{font-size:12px;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--atc-mute)}
.cp-facts dd{margin:var(--sp-2) 0 0;font-size:16px;font-weight:500;color:var(--atc-navy)}
.cp-art{position:relative;aspect-ratio:5/3;border-radius:22px;border:1.5px solid #E7ECF5;overflow:hidden;background:#fff}
.cse-il{position:absolute;inset:0;overflow:hidden;background:linear-gradient(160deg,#F1F6FC,#E4ECF7)}
.il-svg{position:absolute;inset:0;width:100%;height:100%;transform:translateY(4%)}

/* the two figures, in the home page's result cards */
.cp-stats{padding:clamp(16px,3vh,32px) 0}
.cp-stats .cp-in{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,40px)}
.cp-stat{display:flex;flex-direction:column;justify-content:space-between;gap:var(--sp-6);min-height:clamp(180px,26vh,260px);padding:clamp(24px,2.6vw,40px);
  border-radius:22px;border:1.5px solid #E7ECF5;background:#fff}
.cp-stat b{font-weight:400;font-size:clamp(56px,6.4vw,112px);line-height:1;letter-spacing:-.05em;font-variant-numeric:tabular-nums}
.cp-unit{background:var(--atc-grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.cp-stat > span{font-size:16px;font-weight:500;color:var(--atc-slate)}

/* the story: the challenge, who it is for, what we built, what changed */
.cp-sec{padding:clamp(56px,10vh,128px) 0 0}
.cp-row{display:grid;grid-template-columns:minmax(0,.42fr) minmax(0,1fr);gap:var(--sp-6) clamp(32px,5vw,88px);align-items:start}
.cp-row + .cp-row{margin-top:clamp(40px,7vh,88px);padding-top:clamp(40px,7vh,88px);border-top:1px solid #E7ECF5}
.cp-row .cp-label{margin:.55em 0 0}
.cp-statement{margin:0;font-size:var(--fs-h2);line-height:var(--lh-h2);letter-spacing:var(--ls-h2);font-weight:400;color:var(--atc-navy);max-width:24em}
.cp-row .ds-lede{margin:0;max-width:34em;color:var(--atc-slate)}
.cp-hl{list-style:none;margin:var(--sp-7) 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-4)}
.cp-hl li{display:flex;align-items:center;gap:var(--sp-4);padding:20px 22px;border-radius:16px;border:1.5px solid #E7ECF5;background:#fff;font-size:16px;font-weight:500}
.cp-hl i{flex:none;font-style:normal;font-size:12px;font-weight:600;letter-spacing:.06em;background:var(--atc-grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.cp-out{list-style:none;margin:0;padding:0;display:grid;gap:0}
.cp-out li{display:flex;align-items:flex-start;gap:var(--sp-4);padding:20px 0;border-bottom:1px solid #E7ECF5;font-size:var(--fs-body);line-height:1.5;color:var(--atc-navy)}
.cp-out li:first-child{padding-top:4px}
.cp-out svg{flex:none;width:26px;height:26px;padding:5px;border-radius:50%;background:var(--atc-navy);color:#fff;margin-top:-1px}

/* on to the next case */
.cp-more{padding:clamp(72px,12vh,152px) 0 0}
.cp-more .cp-in{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,40px)}
.cp-nav{position:relative;display:flex;flex-direction:column;gap:var(--sp-3);padding:clamp(24px,2.4vw,36px);border-radius:22px;border:1.5px solid #E7ECF5;
  background:#fff;text-decoration:none;transition:border-color .3s ease,box-shadow .3s ease,transform .3s cubic-bezier(.2,.8,.3,1)}
.cp-nav small{font-size:12px;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--atc-mute)}
.cp-nav strong{font-size:var(--fs-h3);line-height:var(--lh-h3);letter-spacing:var(--ls-h3);font-weight:500;color:var(--atc-navy);max-width:20em}
.cp-nav .cp-go{display:inline-flex;align-items:center;gap:10px;margin-top:var(--sp-3);font-size:13px;font-weight:500;color:var(--atc-navy)}
.cp-nav .cp-go svg{box-sizing:content-box;width:10px;height:10px;padding:6px;border-radius:3px;border:1px solid rgba(0,16,37,.18);transition:background-color .3s ease,color .3s ease,border-color .3s ease}
.cp-nav.is-next{text-align:right;align-items:flex-end}
@media (hover:hover){
  .cp-nav:hover{border-color:#D5DEEC;box-shadow:0 28px 50px -34px rgba(0,16,37,.3);transform:translateY(-2px)}
  .cp-nav:hover .cp-go svg{background:var(--atc-navy);border-color:var(--atc-navy);color:#fff}
}

/* the invitation, as the home page ends */
.cp-cta{padding:clamp(72px,12vh,152px) 0}
.cp-cta .cp-in{display:flex;flex-direction:column;align-items:center;text-align:center}
.cp-cta h2{margin:0;max-width:18em;text-wrap:balance}
.cp-cta .ds-btn{margin-top:var(--sp-7)}

/* the footer, as on the home page */
.cp-foot{padding:clamp(48px,8vh,96px) 0 clamp(32px,5vh,56px);border-top:1px solid #E7ECF5}
.cp-foot .cp-in{display:grid;grid-template-columns:minmax(0,1.4fr) repeat(2,minmax(0,auto));gap:var(--sp-7) clamp(40px,7vw,140px);align-items:start}
.cp-foot-claim{margin:0 0 var(--sp-5);font-size:var(--fs-h3);line-height:var(--lh-h3);letter-spacing:var(--ls-h3);font-weight:500;max-width:16em}
.cp-foot address{font-style:normal;color:var(--atc-slate);font-size:var(--fs-body);line-height:1.6}
.cp-foot-legal{margin-top:var(--sp-6);font-size:14px;color:var(--atc-mute)}
.cp-foot-col{display:flex;flex-direction:column;gap:var(--sp-4)}
.cp-foot-col h3{margin:0 0 var(--sp-2);font-size:16px;font-weight:600}
.cp-foot-col a,.cp-foot-col span{font-size:var(--fs-body);color:var(--atc-slate);text-decoration:none;white-space:nowrap;transition:color .25s ease}
.cp-foot-col a:hover{color:var(--atc-navy);text-decoration:underline;text-underline-offset:4px}

/* the buttons, copied from the home page */
.ds-btn{text-decoration:none}
''' + btn + '''
@media (max-width:900px){
  .cp-head .cp-in{height:60px;gap:var(--sp-4)}
  .cp-back span{display:none}
  .cp-hero .cp-in,.cp-row,.cp-more .cp-in,.cp-foot .cp-in{grid-template-columns:minmax(0,1fr)}
  .cp-stats .cp-in{gap:12px}
  .cp-stat{min-height:150px;padding:20px}
  .cp-stat b{font-size:min(56px,11vw)}
  .cp-hl{grid-template-columns:minmax(0,1fr)}
  .cp-nav.is-next{text-align:left;align-items:flex-start}
}
'''

REVEAL = ('<script>(function(){var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("is-in");'
          'o.unobserve(e.target)}})},{rootMargin:"0px 0px -8% 0px"});document.querySelectorAll(".ds-rv").forEach(function(e){o.observe(e)})})();'
          '</script>')


def build(i, c):
    n = len(CASES)
    prev_c, next_c = CASES[(i - 1) % n], CASES[(i + 1) % n]
    num = 'Case %02d' % (i + 1)
    stats = ''.join('<div class="cp-stat ds-rv"><b>%s</b><span>%s</span></div>' % (figure(v), html.escape(l)) for v, l in c['stats'])
    hl = ''.join('<li><i>%02d</i>%s</li>' % (k + 1, html.escape(h)) for k, h in enumerate(c['highlights']))
    out = ''.join('<li>%s<span>%s</span></li>' % (CHECK, html.escape(o)) for o in c['outcomes'])
    t = html.escape(c['title'])
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t} · Case study · ATCON GLOBAL</title>
<meta name="description" content="{html.escape(c['one_liner'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../atcon-ds.css">
<link rel="stylesheet" href="case.css">
</head>
<body data-theme="light">
<header class="cp-head">
  <div class="cp-in">
    <a class="cp-logo" href="../index.html" aria-label="ATCON GLOBAL home">{LOGO}</a>
    <a class="cp-back" href="../index.html#case-studies" aria-label="All case studies">{BACK}<span>All case studies</span></a>
    <a class="ds-btn ds-btn--sm" href="mailto:hello@atconglobal.com">Contact<span class="ds-btn-ic">{ARROW}</span></a>
  </div>
</header>
<main>
  <section class="cp-hero">
    <div class="cp-in">
      <div class="ds-rv">
        <p class="ds-label ds-grad-text cp-label">{num} · {html.escape(c['tag'])}</p>
        <h1 class="ds-display">{t}</h1>
        <p class="ds-lede">{html.escape(c['one_liner'])}</p>
        <dl class="cp-facts"><div><dt>Sector</dt><dd>{html.escape(c['sector'])}</dd></div><div><dt>Focus</dt><dd>{html.escape(c['tag'])}</dd></div></dl>
      </div>
      <div class="cp-art ds-rv"><div class="cse-il">{c['art']}</div></div>
    </div>
  </section>
  <section class="cp-stats" aria-label="In figures"><div class="cp-in">{stats}</div></section>
  <section class="cp-sec">
    <div class="cp-in">
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">The challenge</p><p class="cp-statement">{html.escape(c['problem'])}</p></div>
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">Who it is for</p><p class="ds-lede">{html.escape(c['for_whom'])}</p></div>
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">What we built</p><div><p class="ds-lede">{html.escape(c['built'])}</p><ul class="cp-hl">{hl}</ul></div></div>
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">What changed</p><ul class="cp-out">{out}</ul></div>
    </div>
  </section>
  <nav class="cp-more" aria-label="More case studies">
    <div class="cp-in">
      <a class="cp-nav ds-rv" href="{prev_c['slug']}.html"><small>Previous case</small><strong>{html.escape(prev_c['title'])}</strong><span class="cp-go">{BACK}Read it</span></a>
      <a class="cp-nav is-next ds-rv" href="{next_c['slug']}.html"><small>Next case</small><strong>{html.escape(next_c['title'])}</strong><span class="cp-go">Read it{ARROW}</span></a>
    </div>
  </nav>
  <section class="cp-cta">
    <div class="cp-in ds-rv">
      <h2 class="ds-display">Let’s make technology work for you.</h2>
      <a class="ds-btn" href="mailto:hello@atconglobal.com">Let’s talk<span class="ds-btn-ic">{ARROW}</span></a>
    </div>
  </section>
</main>
<footer class="cp-foot">
  <div class="cp-in">
    <div>
      <p class="cp-foot-claim">The partner that finally works for your business.</p>
      <address>Avenue Louise 523<br>1050 Brussels, Belgium</address>
      <p class="cp-foot-legal">© 2026 ATCON. All rights reserved.</p>
    </div>
    <div class="cp-foot-col"><h3>Explore</h3><a href="../index.html">Home</a><a href="../index.html#case-studies">Case studies</a></div>
    <div class="cp-foot-col"><h3>Contact</h3><a href="mailto:hello@atconglobal.com">hello@atconglobal.com</a><a href="tel:+32470204512">+32 470 20 45 12</a></div>
  </div>
</footer>
{REVEAL}
</body>
</html>
'''


os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'case.css'), 'w', encoding='utf-8', newline='\n').write(CSS)
for i, c in enumerate(CASES):
    open(os.path.join(OUT, c['slug'] + '.html'), 'w', encoding='utf-8', newline='\n').write(build(i, c))

# on the home page, each card's "View case study" becomes the link to its page (the whole card answers to it)
def link(m):
    c = CASES[link.i]; link.i += 1
    body = re.sub(r'<(span|a) class="cs-link"[^>]*>(View case study.*?)</(span|a)>',
                  lambda x: '<a class="cs-link" href="cases/%s.html">%s</a>' % (c['slug'], x.group(2)), m.group(0), flags=re.S)
    return body
link.i = 0
page = re.sub(r'<article class="csf-card">.*?</article>', link, page, flags=re.S)
open(index_path, 'w', encoding='utf-8', newline='').write(page)
print('built', len(CASES), 'case pages in', OUT)
