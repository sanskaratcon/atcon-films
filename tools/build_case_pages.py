"""Builds the v11 case study pages: one page per case, in the home page's own design.

The words come from ATCON's case study library (the Deck of 27 July, rewritten in plain language): who it is for,
the challenge, what we built, the highlights, the outcomes and the two headline figures. Client names are never
used; each story is told by its sector. Each page shows the case's own illustration (taken from its card on the home
page) and its editorial picture from atconglobal.com, and the buttons are the home page's own (their styles are
copied from it), so the pages always match it.

The reading is made to be enjoyed: a thin reading bar, the figures counting up as they arrive, the challenge beside
its picture drifting gently with the scroll, a before-and-after of the change, what we built as building blocks with
their own icons, the outcomes ticking in one by one, and the next case shown with its picture. Everything that moves
is a small layer, so the pages stay light on any machine.

Run from the repository root:  python tools/build_case_pages.py
It writes public/v11/cases/<slug>.html and public/v11/cases/case.css, and turns each case card's "View case study"
on the home page into a link to its page (safe to run again).
"""
import hashlib, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V11 = os.path.join(ROOT, 'public', 'v11')
OUT = os.path.join(V11, 'cases')

# in the order the cards come on the home page; photo: the case's picture from atconglobal.com (public/assets/cases)
CASES = [
    dict(slug='linkedin-lead-generation-agent', sector='B2B sales', tag='Automation', photo='case-3.webp',
         one_liner='AI-driven LinkedIn prospecting that keeps a steady pipeline of qualified B2B leads.',
         for_whom='B2B sales teams that lose time on manual prospecting and inconsistent outreach.',
         problem='Manual prospecting and inconsistent LinkedIn outreach took too much time and produced too few leads.',
         built='An AI agent that finds prospects, personalizes outreach, runs follow-up sequences and alerts the sales team when a prospect shows buying intent.',
         highlights=['AI-powered prospect discovery', 'Personalized outreach at scale', 'Automated follow-up sequences', 'CRM synchronization'],
         outcomes=['Manual outreach replaced by scalable AI-assisted lead generation', 'More engagement through consistent, personalized outreach',
                   'Automated follow-ups that reduce missed opportunities', 'A steady pipeline of qualified B2B leads', 'Sales time spent on high-value conversations'],
         stats=[('24/7', 'Active pipeline'), ('AI', 'Powered agent')]),
    dict(slug='b2b-valuation-platform-strategy', sector='Real estate technology', tag='Platform strategy', photo='case-2.webp',
         one_liner='A platform strategy to embed property valuation tools into partner ecosystems.',
         for_whom='Product companies that want to offer their solution through partners as an embeddable B2B product.',
         problem='A Belgian real estate technology company needed a scalable strategy to launch its property valuation solution as an embeddable B2B product.',
         built='Product advisory, the integration approach, stakeholder alignment and a structured delivery roadmap that made partner adoption straightforward.',
         highlights=['Embeddable B2B product model', 'Freemium access strategy', 'Integration-first thinking', 'Execution clarity and alignment'],
         outcomes=['A clear embeddable product model for partners', 'A freemium access strategy agreed with stakeholders',
                   'An integration-first roadmap the team could execute'],
         stats=[('01', 'Platform strategy'), ('B2B', 'Partner ecosystem')]),
    dict(slug='financial-automation-ecosystem', sector='Accounting and advisory', tag='Automation', photo='case-1.webp',
         one_liner='Automated financial workflows that produce reports, insights and client-ready updates.',
         for_whom='Accounting and advisory firms that spend their time on manual reporting and client communication.',
         problem='Reporting, client communication and financial documentation were manual, which limited efficiency and left data unused.',
         built='An AI-powered automation platform that generates presentation-ready reports, gives advisors an intelligent financial assistant, and creates client-ready newsletters from financial and regulatory updates.',
         highlights=['Context-aware AI assistant', 'Intelligent automation layer', 'Connected data integration'],
         outcomes=['Accounting operations turned into a scalable, insight-led advisory practice', 'Report generation time cut by more than 70 percent',
                   'Faster, clearer and more proactive client communication', 'Instant financial insights inside daily workflows',
                   'Teams shifted to higher-value guidance with data compliance kept'],
         stats=[('70%+', 'Report time reduced'), ('GDPR', 'Compliant')]),
    dict(slug='healthcare-voice-agent', sector='Healthcare', tag='Automation', photo='case-4.webp',
         one_liner='A 24/7 AI voice assistant that answers patient calls and books appointments.',
         for_whom='Clinics, hospital groups and practices with high call volumes and a busy front desk.',
         problem='High call volumes and limited administrative capacity led to missed patient calls and missed appointments.',
         built='An AI voice agent that handles patient calls, schedules and moves appointments, updates the CRM and manages bookings in real time.',
         highlights=['24/7 AI voice agent', 'Automated appointment management', 'Structured data collection', 'Workflow and CRM synchronization'],
         outcomes=['Less administrative work through automated calls and scheduling', 'Staff freed from repetitive tasks to focus on patient care',
                   'Every patient call answered at once, whatever the volume', 'Faster and more accurate appointment management',
                   'Calls, appointments and requests in one system'],
         stats=[('24/7', 'Always available'), ('00', 'Missed calls')]),
    dict(slug='retail-distribution-digitization', sector='Consumer brands and retail', tag='Digital transformation', photo='case-5.webp',
         one_liner='A central mobile platform for real-time sales tracking, schemes and channel operations.',
         for_whom='Consumer brands with retailers, distributors and field sales teams.',
         problem='Retail and distribution operations ran on manual reporting, which meant limited visibility, delayed payouts and inefficient channel management.',
         built='A central, role-based mobile app that digitized sales, schemes and incentive tracking, with real-time analytics, reward redemption and dashboards for every channel stakeholder.',
         highlights=['Role-based dashboards', 'Real-time analytics', 'Instant redemption', 'Unified platform'],
         outcomes=['Manual Excel processes removed across retail and distribution', 'Real-time visibility into sales, schemes and incentives',
                   'Faster payouts and reward redemption across the channel', 'More transparency between retailers, distributors and sales teams',
                   'A scalable digital platform the brand can build on'],
         stats=[('01', 'Unified platform'), ('04', 'Stakeholder roles')]),
    dict(slug='manufacturing-sales-production-automation', sector='Manufacturing', tag='Automation', photo='case-6.webp',
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
CHECK = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path pathLength="1" d="M4 8.4l2.6 2.6L12 5.4"></path></svg>')

# line icons for the building blocks, chosen by the words of each highlight (24 x 24, drawn in the current colour)
ICONS = [
    (('prospect', 'discovery'), '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5 5"/>'),
    (('outreach', 'personal'), '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>'),
    (('follow-up', 'follow up'), '<path d="M19 8a7.5 7.5 0 1 0 1 5"/><path d="M19 3v5h-5"/>'),
    (('voice', '24/7'), '<path d="M5 13a7 7 0 0 1 14 0v4a2 2 0 0 1-2 2h-1v-6h3M5 13h3v6H7a2 2 0 0 1-2-2z"/>'),
    (('appointment',), '<rect x="4" y="5.5" width="16" height="14" rx="2"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4M9 14.5l2 2 4-4"/>'),
    (('data collection',), '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4v2h6V4M8.5 11h7M8.5 14.5h7M8.5 18h4"/>'),
    (('crm', 'sync'), '<path d="M4 12a8 8 0 0 1 13.7-5.6L20 9M20 4v5h-5M20 12a8 8 0 0 1-13.7 5.6L4 15M4 20v-5h5"/>'),
    (('embeddable', 'product model'), '<path d="M10 4h4v3a2 2 0 1 0 4 0V4h2v16H4V4h2v3a2 2 0 1 0 4 0z"/>'),
    (('freemium', 'access'), '<circle cx="8" cy="14" r="4"/><path d="M11 11l8-8M16 6l2 2M14 8l2 2"/>'),
    (('integration',), '<path d="M9 7V3M15 7V3M7 7h10v4a5 5 0 0 1-10 0zM12 16v5"/>'),
    (('execution', 'alignment'), '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".6" fill="currentColor"/>'),
    (('assistant', 'context'), '<path d="M12 3l1.8 4.6L18 9l-4.2 1.4L12 15l-1.8-4.6L6 9l4.2-1.4z"/><path d="M18 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>'),
    (('automation layer', 'automation'), '<path d="M13 3L5 13.5h6L10 21l8-10.5h-6z"/>'),
    (('data integration', 'connected data'), '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>'),
    (('dashboard',), '<rect x="3.5" y="4" width="17" height="16" rx="2"/><path d="M3.5 9.5h17M10 9.5V20"/>'),
    (('analytics',), '<path d="M4 20h16M7 16v-4M11 16V8M15 16v-6M19 16V5"/>'),
    (('redemption',), '<rect x="4" y="9" width="16" height="11" rx="1.5"/><path d="M12 9v11M4 13h16M12 9c-1.5-3-5-3.5-5-1.5S10 9 12 9c2 0 5 .5 5-1.5S13.5 6 12 9z"/>'),
    (('unified', 'platform'), '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 12.5l9 5 9-5M3 16.5l9 5 9-5"/>'),
    (('lead capture',), '<path d="M6 4v8a6 6 0 0 0 12 0V4h-4v8a2 2 0 0 1-4 0V4z"/><path d="M6 8h4M14 8h4"/>'),
    (('workflow',), '<rect x="3" y="4" width="6" height="5" rx="1"/><rect x="15" y="4" width="6" height="5" rx="1"/><rect x="9" y="15" width="6" height="5" rx="1"/><path d="M9 6.5h6M6 9v3.5h6V15M18 9v3.5h-6"/>'),
    (('production',), '<path d="M3 20V10l5 3V10l5 3V7l8-3v16z"/><path d="M7 16.5h2M11.5 16.5h2M16 16.5h2"/>'),
]


def icon(words):
    w = words.lower()
    for keys, body in ICONS:
        if any(k in w for k in keys):
            break
    else:
        body = ICONS[-3][1]
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">%s</svg>' % body)


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
    """the figure in navy, any trailing sign (%, +) in the brand gradient, as on the home page's results; a figure
    that starts with a number counts up to it as it arrives"""
    m = re.match(r'^(\d+)(.*)$', v)
    if not m or int(m.group(1)) < 2:
        u = re.match(r'^(.*?\d)([%+]+)$', v)
        return ('%s<span class="cp-unit">%s</span>' % (html.escape(u.group(1)), html.escape(u.group(2)))) if u else html.escape(v)
    n, rest = m.group(1), m.group(2)
    u = re.match(r'^([%+]+)$', rest)
    tail = '<span class="cp-unit">%s</span>' % html.escape(rest) if u else html.escape(rest)
    return '<span data-count="%d" data-pad="%d">%s</span>%s' % (int(n), len(n), n, tail)


CSS = '''/* Case study pages: the home page's own type, colours, cards and buttons, on white. Built by
   tools/build_case_pages.py - edit there, not here. */
html{scroll-behavior:smooth}
body{margin:0;background:#FFFFFF;color:var(--atc-navy);font-family:var(--atc-font);-webkit-font-smoothing:antialiased}
*{box-sizing:border-box}
a{color:inherit}
.cp-in{width:100%;max-width:1320px;margin:0 auto;padding:0 clamp(20px,5vw,72px)}
.cp-label{margin:0 0 var(--sp-5)}

/* the header: the mark, the way back, and Contact; under it, a thin bar of how far you have read */
.cp-head{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.92);border-bottom:1px solid rgba(0,16,37,.08)}
.cp-head .cp-in{display:flex;align-items:center;gap:var(--sp-6);height:72px}
.cp-read{position:absolute;left:0;right:0;bottom:-1px;height:2px;background:var(--atc-grad);transform:scaleX(0);transform-origin:left;will-change:transform}
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

/* the two figures, in the home page's result cards, counting up as they arrive */
.cp-stats{padding:clamp(16px,3vh,32px) 0}
.cp-stats .cp-in{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,40px)}
.cp-stat{display:flex;flex-direction:column;justify-content:space-between;gap:var(--sp-6);min-height:clamp(180px,26vh,260px);padding:clamp(24px,2.6vw,40px);
  border-radius:22px;border:1.5px solid #E7ECF5;background:#fff}
.cp-stat b{font-weight:400;font-size:clamp(56px,6.4vw,112px);line-height:1;letter-spacing:-.05em;font-variant-numeric:tabular-nums}
.cp-unit{background:var(--atc-grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.cp-stat > span{font-size:16px;font-weight:500;color:var(--atc-slate)}

/* the story */
.cp-sec{padding:clamp(64px,11vh,144px) 0 0}
.cp-row{display:grid;grid-template-columns:minmax(0,.42fr) minmax(0,1fr);gap:var(--sp-6) clamp(32px,5vw,88px);align-items:start}
.cp-row > .cp-label{position:sticky;top:104px;margin:.55em 0 0}
.cp-statement{margin:0;font-size:var(--fs-h2);line-height:var(--lh-h2);letter-spacing:var(--ls-h2);font-weight:400;color:var(--atc-navy);max-width:24em;text-wrap:pretty}
.cp-row .ds-lede{margin:0;max-width:34em;color:var(--atc-slate)}

/* the challenge, beside its picture; the picture drifts a little slower than the page */
.cp-chal{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.86fr);gap:clamp(32px,5vw,88px);align-items:center}
.cp-chal .cp-for{margin-top:var(--sp-7);padding-top:var(--sp-5);border-top:1px solid #E7ECF5}
.cp-chal .cp-for p:last-child{margin:var(--sp-3) 0 0;max-width:30em;color:var(--atc-slate)}
.cp-photo{position:relative;margin:0;aspect-ratio:8/5;border-radius:22px;overflow:hidden;background:#E4ECF7;box-shadow:0 30px 60px -40px rgba(0,16,37,.45)}
.cp-photo img{position:absolute;left:0;top:-6%;width:100%;height:112%;object-fit:cover;display:block;will-change:transform}

/* before and after: the change at a glance */
.cp-ba{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:clamp(12px,2vw,28px);align-items:stretch}
.cp-ba > div{display:flex;flex-direction:column;gap:var(--sp-4);padding:clamp(24px,2.6vw,40px);border-radius:22px}
.cp-before{background:#F4F5F9}
.cp-before p:last-child{color:var(--atc-slate)}
.cp-after{background:var(--atc-navy);color:#fff}
.cp-after .ds-label{color:#9DB8F5}
.cp-ba p{margin:0}
.cp-ba p:last-child{font-size:var(--fs-h3);line-height:1.3;letter-spacing:var(--ls-h3);font-weight:500;max-width:22em}
.cp-ba-arrow{display:flex;align-items:center;justify-content:center}
.cp-ba-arrow span{display:grid;place-items:center;width:48px;height:48px;border-radius:50%;background:#fff;border:1.5px solid #E7ECF5;
  box-shadow:0 16px 30px -20px rgba(0,16,37,.35);color:var(--atc-navy)}
.cp-ba-arrow svg{width:14px;height:14px}

/* what we built: its building blocks, each with its own icon, arriving one after another */
.cp-hl{list-style:none;margin:var(--sp-7) 0 0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--sp-4)}
.cp-hl li{display:flex;align-items:center;gap:var(--sp-4);padding:20px 22px;border-radius:18px;border:1.5px solid #E7ECF5;background:#fff;font-size:16px;font-weight:500;
  opacity:0;transform:translateY(16px);transition:opacity .6s var(--ease-out) calc(var(--i) * 110ms),transform .7s var(--ease-out) calc(var(--i) * 110ms),border-color .3s ease}
.cp-hl.is-in li{opacity:1;transform:none}
.cp-hl li:hover{border-color:#D5DEEC}
.cp-ico{flex:none;display:grid;place-items:center;width:46px;height:46px;border-radius:13px;border:1.5px solid transparent;color:#2D63E6;
  background:linear-gradient(#F3F6FD,#F3F6FD) padding-box,var(--atc-grad) border-box}
.cp-ico svg{width:22px;height:22px}

/* what changed: the outcomes tick in one by one */
.cp-out{list-style:none;margin:0;padding:0;display:grid;gap:0}
.cp-out li{display:flex;align-items:flex-start;gap:var(--sp-4);padding:20px 0;border-bottom:1px solid #E7ECF5;font-size:var(--fs-body);line-height:1.5;color:var(--atc-navy);
  opacity:0;transform:translateX(-10px);transition:opacity .6s var(--ease-out) calc(var(--i) * 140ms),transform .7s var(--ease-out) calc(var(--i) * 140ms)}
.cp-out li:first-child{padding-top:4px}
.cp-out svg{flex:none;width:26px;height:26px;padding:5px;border-radius:50%;background:var(--atc-navy);color:#fff;margin-top:-1px}
.cp-out svg path{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset .5s ease calc(var(--i) * 140ms + .25s)}
.cp-out.is-in li{opacity:1;transform:none}
.cp-out.is-in svg path{stroke-dashoffset:0}

/* on to the next case, each with its picture */
.cp-more{padding:clamp(80px,13vh,168px) 0 0}
.cp-more .cp-in{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2.2vw,40px)}
.cp-nav{position:relative;display:grid;grid-template-columns:minmax(0,1fr) clamp(96px,11vw,152px);gap:var(--sp-5);align-items:center;padding:clamp(18px,1.8vw,26px);
  border-radius:22px;border:1.5px solid #E7ECF5;background:#fff;text-decoration:none;transition:border-color .3s ease,box-shadow .3s ease,transform .3s cubic-bezier(.2,.8,.3,1)}
.cp-nav > div{display:flex;flex-direction:column;gap:var(--sp-3);min-width:0}
.cp-nav small{font-size:12px;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:var(--atc-mute)}
.cp-nav strong{font-size:clamp(17px,1.3vw,22px);line-height:1.25;letter-spacing:var(--ls-h3);font-weight:500;color:var(--atc-navy)}
.cp-nav .cp-go{display:inline-flex;align-items:center;gap:10px;margin-top:var(--sp-2);font-size:13px;font-weight:500;color:var(--atc-navy)}
.cp-nav .cp-go svg{box-sizing:content-box;width:10px;height:10px;padding:6px;border-radius:3px;border:1px solid rgba(0,16,37,.18);transition:background-color .3s ease,color .3s ease,border-color .3s ease}
.cp-thumb{display:block;aspect-ratio:1;overflow:hidden;border-radius:14px;background:#E4ECF7}
.cp-nav img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s cubic-bezier(.2,.8,.3,1)}
.cp-nav.is-prev{grid-template-columns:clamp(96px,11vw,152px) minmax(0,1fr)}
.cp-nav.is-next > div{align-items:flex-end;text-align:right}
@media (hover:hover){
  .cp-nav:hover{border-color:#D5DEEC;box-shadow:0 28px 50px -34px rgba(0,16,37,.3);transform:translateY(-2px)}
  .cp-nav:hover .cp-go svg{background:var(--atc-navy);border-color:var(--atc-navy);color:#fff}
  .cp-nav:hover img{transform:scale(1.06)}
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
  .cp-hero .cp-in,.cp-row,.cp-chal,.cp-more .cp-in,.cp-foot .cp-in{grid-template-columns:minmax(0,1fr)}
  .cp-row > .cp-label{position:static}
  .cp-stats .cp-in{gap:12px}
  .cp-stat{min-height:150px;padding:20px}
  .cp-stat b{font-size:min(56px,11vw)}
  .cp-ba{grid-template-columns:minmax(0,1fr)}
  .cp-ba-arrow span{transform:rotate(90deg)}
  .cp-hl{grid-template-columns:minmax(0,1fr)}
  .cp-nav,.cp-nav.is-prev{grid-template-columns:88px minmax(0,1fr)}
  .cp-nav.is-next .cp-thumb{order:-1}
  .cp-nav.is-next > div{align-items:flex-start;text-align:left}
}
'''

# the page's small motions: reveals, the reading bar, the figures counting up, the picture's drift
SCRIPT = '''<script>
(function () {
  var o = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in'); o.unobserve(e.target);
      [].forEach.call(e.target.querySelectorAll('[data-count]'), count);
    });
  }, { rootMargin: '0px 0px -10% 0px' });
  [].forEach.call(document.querySelectorAll('.ds-rv, .cp-hl, .cp-out'), function (e) { o.observe(e); });
  function count(el) {
    var to = +el.getAttribute('data-count'), pad = +el.getAttribute('data-pad'), t0 = performance.now();
    (function step(now) {
      var k = Math.min(1, (now - t0) / 1400), v = Math.round(to * (1 - Math.pow(1 - k, 3))), s = String(v);
      while (s.length < pad) s = '0' + s;
      el.textContent = s;
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  var bar = document.querySelector('.cp-read'), pic = document.querySelector('.cp-photo img'), raf = 0, lastB = '', lastP = '';
  function frame() {
    raf = 0;
    var de = document.documentElement, max = Math.max(1, de.scrollHeight - innerHeight);
    var b = 'scaleX(' + Math.min(1, scrollY / max).toFixed(4) + ')';
    if (bar && b !== lastB) { bar.style.transform = b; lastB = b; }
    if (pic) {
      var r = pic.parentNode.getBoundingClientRect(), n = (r.top + r.height / 2 - innerHeight / 2) / innerHeight;
      var p = 'translate3d(0,' + Math.round(Math.max(-1, Math.min(1, n)) * -18) + 'px,0)';
      if (p !== lastP) { pic.style.transform = p; lastP = p; }
    }
  }
  function req() { if (!raf) raf = requestAnimationFrame(frame); }
  addEventListener('scroll', req, { passive: true }); addEventListener('resize', req); req();
})();
</script>'''


def build(i, c):
    n = len(CASES)
    prev_c, next_c = CASES[(i - 1) % n], CASES[(i + 1) % n]
    num = 'Case %02d' % (i + 1)
    stats = ''.join('<div class="cp-stat ds-rv"><b>%s</b><span>%s</span></div>' % (figure(v), html.escape(l)) for v, l in c['stats'])
    hl = ''.join('<li style="--i:%d"><span class="cp-ico">%s</span>%s</li>' % (k, icon(h), html.escape(h)) for k, h in enumerate(c['highlights']))
    out = ''.join('<li style="--i:%d">%s<span>%s</span></li>' % (k, CHECK, html.escape(o)) for k, o in enumerate(c['outcomes']))
    t = html.escape(c['title'])

    def nav(cc, kind, label):
        thumb = '<span class="cp-thumb"><img src="../../assets/cases/%s" alt="" width="640" height="400" loading="lazy" decoding="async"></span>' % cc['photo']
        go = ('%sRead it' % BACK) if kind == 'prev' else ('Read it%s' % ARROW)
        txt = '<div><small>%s</small><strong>%s</strong><span class="cp-go">%s</span></div>' % (label, html.escape(cc['title']), go)
        return '<a class="cp-nav is-%s ds-rv" href="%s.html">%s</a>' % (kind, cc['slug'], (thumb + txt) if kind == 'prev' else (txt + thumb))

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
<link rel="stylesheet" href="case.css?v={CSS_V}">
</head>
<body data-theme="light">
<header class="cp-head">
  <div class="cp-in">
    <a class="cp-logo" href="../index.html" aria-label="ATCON GLOBAL home">{LOGO}</a>
    <a class="cp-back" href="../index.html#case-studies" aria-label="All case studies">{BACK}<span>All case studies</span></a>
    <a class="ds-btn ds-btn--sm" href="mailto:hello@atconglobal.com">Contact<span class="ds-btn-ic">{ARROW}</span></a>
  </div>
  <i class="cp-read" aria-hidden="true"></i>
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
    <div class="cp-in cp-chal">
      <div class="ds-rv">
        <p class="ds-label ds-grad-text cp-label">The challenge</p>
        <p class="cp-statement">{html.escape(c['problem'])}</p>
        <div class="cp-for"><p class="ds-label ds-grad-text">Who it is for</p><p class="ds-lede">{html.escape(c['for_whom'])}</p></div>
      </div>
      <figure class="cp-photo ds-rv"><img src="../../assets/cases/{c['photo']}" alt="" width="640" height="400" decoding="async"></figure>
    </div>
  </section>
  <section class="cp-sec" aria-label="Before and after">
    <div class="cp-in cp-ba ds-rv">
      <div class="cp-before"><p class="ds-label">Before</p><p>{html.escape(c['problem'])}</p></div>
      <div class="cp-ba-arrow" aria-hidden="true"><span>{ARROW}</span></div>
      <div class="cp-after"><p class="ds-label">After</p><p>{html.escape(c['outcomes'][0])}</p></div>
    </div>
  </section>
  <section class="cp-sec">
    <div class="cp-in">
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">What we built</p><div><p class="ds-lede">{html.escape(c['built'])}</p><ul class="cp-hl">{hl}</ul></div></div>
    </div>
  </section>
  <section class="cp-sec">
    <div class="cp-in">
      <div class="cp-row ds-rv"><p class="ds-label ds-grad-text cp-label">What changed</p><ul class="cp-out">{out}</ul></div>
    </div>
  </section>
  <nav class="cp-more" aria-label="More case studies">
    <div class="cp-in">{nav(prev_c, 'prev', 'Previous case')}{nav(next_c, 'next', 'Next case')}</div>
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
{SCRIPT}
</body>
</html>
'''


os.makedirs(OUT, exist_ok=True)
# (the pages ask for the stylesheet by a fingerprint of its contents, so a browser never keeps an old one)
CSS_V = hashlib.md5(CSS.encode('utf-8')).hexdigest()[:8]
open(os.path.join(OUT, 'case.css'), 'w', encoding='utf-8', newline='\n').write(CSS)
for i, c in enumerate(CASES):
    assert os.path.exists(os.path.join(ROOT, 'public', 'assets', 'cases', c['photo'])), c['photo']
    open(os.path.join(OUT, c['slug'] + '.html'), 'w', encoding='utf-8', newline='\n').write(build(i, c))


# on the home page, each card's "View case study" becomes the link to its page (the whole card answers to it)
def link(m):
    c = CASES[link.i]; link.i += 1
    return re.sub(r'<(span|a) class="cs-link"[^>]*>(View case study.*?)</(span|a)>',
                  lambda x: '<a class="cs-link" href="cases/%s.html">%s</a>' % (c['slug'], x.group(2)), m.group(0), flags=re.S)


link.i = 0
page = re.sub(r'<article class="csf-card">.*?</article>', link, page, flags=re.S)
open(index_path, 'w', encoding='utf-8', newline='').write(page)
print('built', len(CASES), 'case pages in', OUT)
