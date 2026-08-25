"""Gradio front end. All logic is reused from main.py."""
import gradio as gr
from main import (
    predict_price, estimate_price, browse_listings,
    ListingRequest, EstimateRequest, KNOWN_AREAS,
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
    colour = COLOUR.get(d.get("position"), "#33566B")
    head = (f"<p class='title'>{d.get('title') or ''}</p>"
            f"<p class='meta'>{d['area']} · {d['property_type']} · {d['size_marla']} marla</p>")

    if not c:
        return (f"<div class='card'><div class='pad'>{head}"
                f"<p class='lede'>Not enough similar listings to say anything useful.</p>"
                f"<p class='lede-2'>Fewer than five comparable properties in "
                f"{d['area']} at this size.</p></div></div>")

    ask = d.get("asking_price")
    if ask is None:
        lede = f"<p class='lede'>Similar properties here ask <b>{pkr(c['typical'])}</b> on average.</p>"
    else:
        pct = round(abs(ask - c["typical"]) / c["typical"] * 100)
        dirn = "more" if ask >= c["typical"] else "less"
        phrase = {"within": "in line", "above": "more than usual", "below": "less than usual"}
        word = phrase.get(d.get("position"), "in line")
        tail = "with similar listings" if d.get("position") == "within" else "around here"
        lede = (f"<p class='lede'><b>{pkr(ask)}</b> is "
                f"<span class='hl' style='color:{colour}'>{word}</span> {tail}.</p>"
                f"<p class='lede-2'>That's {pct}% {dirn} than the {pkr(c['typical'])} typical "
                f"for {d['size_marla']} marla {d['property_type'].lower()}s in {d['area']}.</p>")

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
              f"{c['size_range_marla'][1]} marla in {d['area']}.{thin} The model estimate is "
              f"usually within about 15%; the range is the more reliable figure.</p></div>")


def check_url(url):
    if not url or "zameen.com" not in url:
        return "<div class='msg'>Paste a zameen.com listing link.</div>", []
    d = predict_price(ListingRequest(url=url.strip()))
    return card_html(d), (d.get("images") or [])


def check_details(area, ptype, size, beds, baths):
    if not area:
        return "<div class='msg'>Pick an area from the list.</div>"
    if not size:
        return "<div class='msg'>Enter a size in marla.</div>"
    d = estimate_price(EstimateRequest(
        area=area, property_type=ptype, size_marla=float(size),
        beds=float(beds) if beds else None,
        baths=float(baths) if baths else None))
    return card_html(d)


def browse(position, area):
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
    return header + "".join(rows)


with gr.Blocks(title="Is this Lahore listing priced like its neighbours?") as demo:
    gr.Markdown(
        "# Is this listing priced like its neighbours?\n"
        "Compares any Lahore property against real Zameen listings of similar size "
        "in the same area. Built on 13,203 listings."
    )

    with gr.Tab("Paste a link"):
        url_in = gr.Textbox(label="Zameen listing link",
                            placeholder="https://www.zameen.com/Property/...")
        url_btn = gr.Button("Check this listing", variant="primary")
        url_gallery = gr.Gallery(label="Photos", columns=4, height=260, show_label=False)
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
            barea_in = gr.Dropdown(choices=[""] + KNOWN_AREAS, value="",
                                   label="Area (blank = all)", filterable=True)
        br_btn = gr.Button("Show listings", variant="primary")
        br_out = gr.HTML()
        br_btn.click(browse, [pos_in, barea_in], br_out)

    gr.Markdown(
        "These are prices sellers *ask*, not what properties sell for — Pakistan keeps no "
        "public record of sale prices. Use it as a second opinion before you call an agent."
    )

if __name__ == "__main__":
    demo.launch(css=CSS, ssr_mode=False)