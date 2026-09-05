"""Gradio front end. All logic is reused from main.py."""
import gradio as gr
from main import (
    predict_price, estimate_price, browse_listings,
    ListingRequest, EstimateRequest, KNOWN_AREAS, BROWSE_AREAS, COMPS, BROWSE_AREAS_ABOVE,
    BROWSE_AREAS_BELOW
)

try:
    import spaces

    @spaces.GPU
    def _gpu_stub():
        """ZeroGPU requires at least one GPU-decorated function. Never called."""
        return "ok"
except ImportError:
    pass          # not running on Hugging Face

CSS = """
.gradio-container {max-width: 720px !important}
.card, .card *, .listing, .listing *, .msg, .msg * {color:#12262E !important}
.card {background:#fff;border:1px solid #C9D4D3;border-radius:2px;overflow:hidden;
       margin-top:6px;font-family:system-ui,sans-serif}
.card .pad{padding:18px}
.card .title{font-weight:600;font-size:16px;line-height:1.3;margin:0 0 3px}
.card .meta{font-size:13px;color:#3A5560 !important;margin:0}
.lede{font-size:21px;line-height:1.32;margin:16px 0 0}
.lede b{font-weight:800}
.lede .hl{border-bottom:3px solid currentColor}
.lede-2{font-size:14.5px;color:#3A5560 !important;margin:8px 0 0}
.figs{display:flex;gap:22px;margin-top:20px;padding-top:16px;
      border-top:1px solid #C9D4D3;flex-wrap:wrap}
.fig .k{font-size:11px;color:#3A5560 !important;text-transform:uppercase;letter-spacing:.06em}
.fig .v{font-size:17px;font-weight:500;font-variant-numeric:tabular-nums}
.proof{border-top:1px solid #C9D4D3;padding:16px 18px 6px;background:#FAFBFB}
.proof h4{font-size:11px;letter-spacing:.12em;text-transform:uppercase;
          color:#3A5560 !important;font-weight:500;margin:0 0 10px}
.comp{display:flex;justify-content:space-between;gap:12px;padding:7px 0;
      border-bottom:1px dotted #C9D4D3;text-decoration:none;font-size:13.5px;text-align:left}
.comp:hover span:first-child{text-decoration:underline}
.note{font-size:12.5px;color:#3A5560 !important;padding:12px 18px 18px;margin:0}
.listing{display:flex;gap:12px;text-decoration:none;background:#fff;
         border:1px solid #C9D4D3;border-left:3px solid #999;padding:12px;
         margin-bottom:9px;align-items:flex-start;font-family:system-ui,sans-serif}
.listing img{width:78px;height:62px;object-fit:cover;flex:none;background:#DCE5E3}
.listing h3{font-size:14px;font-weight:500;margin:0 0 6px;line-height:1.35;text-align:left}
.nums{display:flex;gap:14px;font-size:12px;flex-wrap:wrap}
.nums span{color:#3A5560 !important}
.nums b{color:#12262E !important;font-weight:600}
.msg{padding:15px;background:#fff;border:1px solid #C9D4D3;
     border-left:3px solid #A97B29;font-size:14px}
.about {font-family:system-ui,sans-serif;color:#12262E !important;line-height:1.55;
        font-size:14.5px;max-width:640px}
.about h3 {font-size:15px;margin:26px 0 8px;color:#12262E !important}
.about h3:first-child {margin-top:6px}
.about p {margin:0 0 11px;color:#2A4550 !important}
.about b {color:#12262E !important}
.about .lead {font-size:16.5px;color:#12262E !important;margin-bottom:16px}
.about {font-family:system-ui,sans-serif;color:#12262E !important;line-height:1.55;
        font-size:14.5px;max-width:640px;background:#fff;padding:20px;
        border:1px solid #C9D4D3}
footer {display:none !important}
.gradio-container {padding-top:8px !important}
h1 {font-size:26px !important;line-height:1.25 !important;margin-bottom:4px !important}

"""

COLOUR = {"above": "#B23A48", "below": "#1F7A5C", "within": "#33566B"}


def pkr(n):
    if n is None:
        return "—"
    if n >= 1e7:
        return f"{n/1e7:.2f}".rstrip("0").rstrip(".") + " cr"
    if n >= 1e5:
        return f"{n/1e5:.1f}".rstrip("0").rstrip(".") + " lakh"
    return f"{n:,.0f}"


def card_html(d):
    if d.get("error"):
        return f"<div class='msg'>{d['error']}</div>"

    c = d.get("comparables")
    scope_label = d['area']
    if c and c.get("scope") == "block" and c.get("block"):
        scope_label = f"{d['area']}, {c['block']}"
    colour = COLOUR.get(d.get("position"), "#33566B")
    head = (f"<p class='title'>{d.get('title') or ''}</p>"
            f"<p class='meta'>{scope_label} · {d['property_type']} · {d['size_marla']} marla</p>")

    if not c:
        size = d.get('size_marla')
        where = d['area'] if d['area'] != 'Other' else 'this area'
        if d['area'] == 'Other':
            why = ("This area has too few listings in the dataset to compare "
                   "against.")
        else:
            why = (f"Properties around {size} marla are uncommon in {where}, "
                   f"so there are fewer than five to compare against.")
        ac = d.get("area_context")
        extra = ""
        if ac:
            extra = (f"<p class='lede-2'>For wider context, houses in {d['area']} ask "
                     f"<b>{pkr(ac['ppm_low'])} to {pkr(ac['ppm_high'])} per marla</b>, "
                     f"typically {pkr(ac['ppm_typical'])}. That is across {ac['count']} "
                     f"listings of {ac['size_low']:.0f} to {ac['size_high']:.0f} marla, "
                     f"and rates fall as size rises, so it is a rough anchor rather "
                     f"than a price for this property.</p>")
        return (f"<div class='card'><div class='pad'>{head}"
                f"<p class='lede'>No verdict on this one.</p>"
                f"<p class='lede-2'>{why} A judgement from two or three "
                f"listings would be worse than none.</p>{extra}</div></div>")


    ask = d.get("asking_price")
    if ask is None:
        lede = f"<p class='lede'>Similar properties here ask <b>{pkr(c['typical'])}</b> on average.</p>"
    elif d.get("implausible"):
        # Far below everything comparable: almost always a typo or a property
        # that is not comparable. Show the figures, but do not call it a bargain.
        lede = (f"<p class='lede'><b>{pkr(ask)}</b> is far below everything "
                f"comparable nearby.</p>"
                f"<p class='lede-2'>That usually means a typo in the listing, or a "
                f"property that is not comparable, such as a plot rather than a "
                f"house. The figures below are real; judge for yourself.</p>")
    else:
        pct = round(abs(ask - c["typical"]) / c["typical"] * 100)
        dirn = "more" if ask >= c["typical"] else "less"
        phrase = {"within": "in line", "above": "more than usual", "below": "less than usual"}
        word = phrase.get(d.get("position"), "in line")
        tail = "with similar listings" if d.get("position") == "within" else "around here"
        lede = (f"<p class='lede'><b>{pkr(ask)}</b> is "
                f"<span class='hl' style='color:{colour}'>{word}</span> {tail}.</p>"
                f"<p class='lede-2'>That's {pct}% {dirn} than the {pkr(c['typical'])} typical "
                f"for {d['size_marla']} marla {d['property_type'].lower()}s in {scope_label}.</p>")
        if d.get("position") == "below":
            lede += ("<p class='lede-2'>Unusually low asking prices are sometimes bait: "
                     "the listing gets you to call, then you are told it is sold. "
                     "Worth confirming it is real before you make plans.</p>")

    examples = "".join(
        f"<a class='comp' href='{e['url']}' target='_blank'>"
        f"<span>{e['title']}</span><span>{pkr(e['price'])}</span></a>"
        for e in (c.get("examples") or [])
    )

    figs = ""
    if ask:
        figs += f"<div class='fig'><div class='k'>Asking</div><div class='v'>{pkr(ask)}</div></div>"
    figs += (f"<div class='fig'><div class='k'>Typical</div><div class='v'>{pkr(c['typical'])}</div></div>"
             f"<div class='fig'><div class='k'>Usual range</div>"
             f"<div class='v'>{pkr(c['low'])} – {pkr(c['high'])}</div></div>"
             f"<div class='fig'><div class='k'>Model estimate</div>"
             f"<div class='v'>{pkr(d['predicted_price'])}</div></div>")

    thin = " Only a handful, so read it loosely." if d.get("confidence") == "low" else ""
    return (f"<div class='card'><div class='pad'>{head}{lede}"
            f"<div class='figs'>{figs}</div></div>"
            + (f"<div class='proof'><h4>The closest listings this is measured against</h4>{examples}</div>"
               if examples else "")
            + f"<p class='note'>From {c['count']} listings of {c['size_range_marla'][0]}–"
              f"{c['size_range_marla'][1]} marla in {scope_label}.{thin} The model estimate is "
              f"usually within about 15%; the range is the more reliable figure.</p></div>")

import json


def check_url_json(url):
    """Same as check_url but returns the raw verdict as JSON, for the custom
    frontend. The card is built in JavaScript there, so no HTML is produced
    here: two implementations of the card would drift, which is a pattern this
    project has already hit four times."""
    print("RUN: check_url_json", flush=True)
    if not url or "zameen.com" not in url:
        return json.dumps({"error": "Paste a zameen.com listing link."})
    d = predict_price(ListingRequest(url=url.strip()))
    d.pop("scraped_raw", None)          # large and not needed by the frontend
    return json.dumps(d, default=str)

def check_url(url):
    print("RUN: check_url", flush=True)
    if not url or "zameen.com" not in url:
        return "<div class='msg'>Paste a zameen.com listing link.</div>", gr.update(visible=False)
    d = predict_price(ListingRequest(url=url.strip()))
    images = d.get("images") or []
    return card_html(d), gr.update(value=images, visible=bool(images))


def check_details(area, ptype, size, beds, baths):
    print("RUN: check_url", flush=True)
    if not area:
        return "<div class='msg'>Pick an area from the list.</div>"
    if not size:
        return "<div class='msg'>Enter a size in marla.</div>"
    d = estimate_price(EstimateRequest(
        area=area, property_type=ptype, size_marla=float(size),
        beds=float(beds) if beds else None,
        baths=float(baths) if baths else None))
    return card_html(d)

def swap_areas(position):
    areas = BROWSE_AREAS_ABOVE if position.startswith("Asking more") else BROWSE_AREAS_BELOW
    return gr.update(choices=[""] + areas, value="")

def browse(position, area):
    print("RUN: check_url", flush=True)
    pos = "above" if position.startswith("Asking more") else "below"
    d = browse_listings(position=pos, area=(area or None), limit=15)
    if d.get("error") or not d.get("listings"):
        return "<div class='msg'>Nothing matches that. Try another area.</div>"
    col = COLOUR[pos]
    word = "more" if pos == "above" else "less"
    rows = []
    for l in d["listings"]:
        img = (f"<img src='{l['image']}' loading='lazy'>"
               if l.get("image") and isinstance(l["image"], str) else "")
        ratio = l["asking_price"] / l["comp_typical"] if l.get("comp_typical") else 0
        model_bit = (f"<span>model says <b>{pkr(l.get('predicted_price'))}</b></span>"
                     if l.get("predicted_price") else "")
        rows.append(
            f"<a class='listing' href='{l['url']}' target='_blank' style='border-left-color:{col}'>"
            f"{img}<div><h3>{l['title']}</h3><div class='nums'>"
            f"<span>asks <b>{pkr(l['asking_price'])}</b></span>"
            f"<span>similar ask <b>{pkr(l['comp_typical'])}</b></span>{model_bit}"
            f"<span style='color:{col}'><b>{ratio:.1f}× typical</b></span>"
            f"</div></div></a>")
    header = (f"<p style='font-size:12px;letter-spacing:.12em;text-transform:uppercase;"
              f"color:#3A5560'>{d['count']} listings asking well {pos} what similar-sized "
              f"listings nearby ask</p>")
    if pos == "below":
        header += ("<p style='font-size:12.5px;color:#3A5560'>Some of these are "
                   "genuine, some are bait. Dealers post an attractive price to "
                   "get a call, then say it has sold.</p>")
    return header + "".join(rows)


THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.slate,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.gray,
    font=("system-ui", "sans-serif"),
).set(
    body_background_fill="#F4F6F6",
    block_background_fill="#FFFFFF",
    button_primary_background_fill="#12262E",
    button_primary_background_fill_hover="#1F3D48",
    button_primary_text_color="#FFFFFF",
    block_border_width="1px",
    block_radius="2px",
)

with gr.Blocks(title="Is this Lahore listing priced like its neighbours?") as demo:
    gr.Markdown(
        "# Is this listing priced like its neighbours?\n"
        "Compares any Lahore property against real Zameen listings of similar size "
        f"in the same area. Built on {len(COMPS):,} listings."
    )

    with gr.Tab("Paste a link"):
        url_in = gr.Textbox(label="Zameen listing link",
                            placeholder="https://www.zameen.com/Property/...")
        url_btn = gr.Button("Check this listing", variant="primary")
        url_gallery = gr.Gallery(label="Photos", columns=4, height=260,show_label=False, visible=False)
        url_out = gr.HTML()
        url_btn.click(check_url, url_in, [url_out, url_gallery])

    with gr.Tab("Enter details"):
        area_in = gr.Dropdown(choices=KNOWN_AREAS, label="Area", filterable=True)
        with gr.Row():
            ptype_in = gr.Radio(["House", "Flat"], value="House", label="Type")
            size_in = gr.Number(label="Size (marla)", value=10)
        with gr.Row():
            beds_in = gr.Number(label="Bedrooms", value=None)
            baths_in = gr.Number(label="Bathrooms", value=None)
        det_btn = gr.Button("Show the typical range", variant="primary")
        det_out = gr.HTML()
        det_btn.click(check_details, [area_in, ptype_in, size_in, beds_in, baths_in], det_out)

    with gr.Tab("Browse"):
        with gr.Row():
            pos_in = gr.Radio(["Asking more than their area", "Asking less than their area"],
                              value="Asking more than their area", label="Show listings")
            barea_in = gr.Dropdown(choices=[""] + BROWSE_AREAS_ABOVE, value="",
                                   label="Area (blank = all)", filterable=True)

        br_btn = gr.Button("Show listings", variant="primary")
        br_out = gr.HTML()
        br_btn.click(browse, [pos_in, barea_in], br_out)
        pos_in.change(swap_areas, pos_in, barea_in)

    with gr.Tab("About"):
            gr.HTML(f"""
    <div class='about'>

    <p class='lead'>Paste a Zameen listing link and this shows you what comparable
    properties in the same area and size are asking, and where that listing sits
    among them.</p>

    <h3>Why it exists</h3>
    <p>Pakistan keeps no public record of what properties actually sell for. There is
    no registry a buyer can check. What exists is what sellers ask, and asking prices
    for near-identical properties vary enormously.</p>
    <p>In DHA Phase 6 Block K, 2-kanal houses with six bedrooms are currently listed
    anywhere between 15 crore and 65 crore. Same block, same size, same bedroom count.
    Some of that gap is real, and some of it is that nobody can check.</p>
    <p>So this cannot tell you what a house is worth. Nobody can, honestly, with the
    data that exists here. What it can do is bound the question.</p>
    <p>Say you are told 2.85 crore is fair for a 5-marla house in Central Park Block A1,
    and four comparable houses on that block are listed at 2.2 to 2.44. You do not know
    2.85 is wrong. You know it needs a reason. Maybe the finish justifies it, maybe it
    does not. Either way you now ask a question you would not have asked, and the seller
    has to answer it.</p>

    <h3>What you get</h3>
    <p><b>A range.</b> The 15th to 85th percentile of asking prices for properties of
    similar size in the same area. Where the listing names a block, it compares within
    the block, which is narrower and more useful.</p>
    <p><b>The comparables themselves</b>, with links, so you can open them and judge
    whether the comparison is fair.</p>
    <p><b>A model estimate</b>, shown last and deliberately so. The range is built from
    real listings and is the more reliable figure.</p>

    <h3>What it cannot do</h3>
    <p><b>It is not a valuation.</b> It compares asking prices to asking prices. If
    everyone in an area is asking too much, it will tell you a listing is normal.</p>
    <p><b>It cannot see the house.</b> Two houses of the same size on the same block
    can differ two or three times in price because of construction, finish and
    condition. If a listing sits above the range, it might simply be better.</p>
    <p><b>Out of range does not mean overpriced.</b> It means fewer than 15% of
    comparable listings ask this much. A question worth asking, not an answer.</p>
    <p><b>Unusually low prices are sometimes bait.</b> Dealers post an attractive price
    to get you to call, then say it has sold and offer something else.</p>
    <p><b>Some properties get no verdict.</b> With fewer than five genuine comparables
    it says so rather than guessing. A judgement from two listings would be worse
    than none.</p>

    <h3>The data</h3>
    <p>{len(COMPS):,} listings scraped from Zameen, covering houses and flats across
    {len(KNOWN_AREAS)} areas of Lahore. Plots, farm houses and portions are not
    covered, since they price on different logic. Installment-plan listings are
    excluded, because the figure quoted is a payment plan rather than a sale price.</p>
    <p>This is a snapshot rather than a live feed, so a listing may have sold or been
    withdrawn since it was collected.</p>

    <h3>Who made this</h3>
    <p>I am an AI student in Lahore. I built this because the property market here runs
    on information nobody outside it can check.</p>
    <p>A friend who tested an early version put it better than I could: it helps you
    get away from the bogus talk of dealers. That is the whole idea. It will not
    replace an agent and it will not tell you what to pay. It is a second opinion to
    have in hand before you make the call.</p>
    <p>It is free, it has no ads, and it sells nothing to anyone. If it is useful, or
    if it gets something wrong, I would rather know.</p>

    </div>
    """)

    with gr.Row(visible=False):
        api_in = gr.Textbox()
        api_out = gr.Textbox()
        api_btn = gr.Button()
        api_btn.click(check_url_json, api_in, api_out, api_name="check_url_json")

    gr.Markdown(
        "These are prices sellers *ask*, not what properties sell for — Pakistan keeps no "
        "public record of sale prices. Use it as a second opinion before you call an agent."
    )

if __name__ == "__main__":
    demo.launch(css=CSS, theme=THEME, ssr_mode=False)