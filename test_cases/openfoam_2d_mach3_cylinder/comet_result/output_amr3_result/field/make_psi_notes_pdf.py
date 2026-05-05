#!/usr/bin/env python3
"""Build a PDF that bundles the physics interpretation, Q&A notes, and
slide-ready talking points for the 1 mm nozzle plume impinging on a flat
surface (plume-surface interaction study)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem, KeepTogether,
)
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER


OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "PSI_physics_notes.pdf",
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Body", parent=styles["BodyText"],
    fontName="Helvetica", fontSize=10.5, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="H1", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=16, leading=20,
    spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1a365d"),
))
styles.add(ParagraphStyle(
    name="H2", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=13, leading=17,
    spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#2c5282"),
))
styles.add(ParagraphStyle(
    name="H3", parent=styles["Heading3"],
    fontName="Helvetica-Bold", fontSize=11, leading=14,
    spaceBefore=7, spaceAfter=3, textColor=colors.HexColor("#2b6cb0"),
))
styles.add(ParagraphStyle(
    name="Quote", parent=styles["BodyText"],
    fontName="Helvetica-Oblique", fontSize=10.5, leading=14,
    leftIndent=16, rightIndent=16, spaceBefore=5, spaceAfter=8,
    textColor=colors.HexColor("#333333"),
    borderColor=colors.HexColor("#888888"), borderPadding=6,
    borderWidth=0.5, backColor=colors.HexColor("#f7f7f7"),
))
styles.add(ParagraphStyle(
    name="Title1", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=22, leading=28,
    alignment=TA_CENTER, spaceAfter=10,
    textColor=colors.HexColor("#1a365d"),
))
styles.add(ParagraphStyle(
    name="Subtitle", parent=styles["Normal"],
    fontName="Helvetica-Oblique", fontSize=12, leading=16,
    alignment=TA_CENTER, textColor=colors.HexColor("#444444"),
    spaceAfter=18,
))

story = []
P = lambda t: Paragraph(t, styles["Body"])
H1 = lambda t: Paragraph(t, styles["H1"])
H2 = lambda t: Paragraph(t, styles["H2"])
H3 = lambda t: Paragraph(t, styles["H3"])
Q = lambda t: Paragraph(t, styles["Quote"])


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(it, styles["Body"]), leftIndent=14) for it in items],
        bulletType="bullet", leftIndent=14, bulletFontName="Helvetica",
        bulletFontSize=10,
    )


def make_table(data, col_widths=None, header=True):
    tbl = Table(data, colWidths=col_widths, hAlign="LEFT")
    ts = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888888")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        ts += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.5),
        ]
    tbl.setStyle(TableStyle(ts))
    return tbl


# ----------------------------------------------------------------------
# Cover
# ----------------------------------------------------------------------
story += [
    Spacer(1, 1.5 * cm),
    Paragraph("Plume-Surface Interaction: Physics Notes", styles["Title1"]),
    Paragraph(
        "1 mm nozzle plume impinging on a flat surface &mdash; "
        "interpretation of density, translational temperature, velocity, "
        "surface pressure, surface shear and heat flux",
        styles["Subtitle"],
    ),
    Spacer(1, 0.4 * cm),
    Paragraph(
        "Companion notes for the AMR DSMC simulation results "
        "(<font face='Courier'>den112</font>, "
        "<font face='Courier'>trans112</font>, "
        "<font face='Courier'>velocity112</font>) "
        "in <font face='Courier'>openfoam_mach3_cylinder / "
        "comet_result / output_amr3_result / field</font>.",
        styles["Body"],
    ),
    PageBreak(),
]

# ----------------------------------------------------------------------
# 1. Slide-ready 3 points
# ----------------------------------------------------------------------
story += [
    H1("1. Slide-ready talking points (3 headline bullets)"),
    H2("Slide 1 &mdash; Plume expansion and recompression shock"),
    P("Files referenced: <font face='Courier'>den112.png</font>, "
      "<font face='Courier'>trans112.png</font>."),
    bullets([
        "Centerline density drops by orders of magnitude from nozzle "
        "(Location&nbsp;3) to plate (Location&nbsp;1) &mdash; rapid near-field "
        "expansion of the 1&nbsp;mm plume.",
        "Deep cold spot on the axis followed by a broad T<sub>x</sub> peak at "
        "Locations&nbsp;3/4/2 &mdash; barrel/reflected shock recompression, "
        "not free expansion alone.",
    ]),

    H2("Slide 2 &mdash; Impingement builds a wall-jet on the plate"),
    P("Files referenced: <font face='Courier'>velocity112.png</font>."),
    bullets([
        "At the surface (Location&nbsp;1): U &asymp; 0 on axis (stagnation), "
        "rising to an off-axis maximum &mdash; classic wall-jet after impact.",
        "Upper probes (Locations&nbsp;3/4/2) still show a jet-core peak on axis "
        "&mdash; the momentum source that drives the surface loading below.",
    ]),

    H2("Slide 3 &mdash; 2D axisymmetric &equiv; 3D for this geometry"),
    P("Files referenced: all three plots."),
    bullets([
        "Solid (2D) and dashed (3D) curves nearly overlap at every height in "
        "&rho;, T<sub>x</sub>, and U.",
        "2D is sufficient for parametric PSI sweeps; 3D only required if "
        "azimuthal asymmetry (tilted plate, off-axis nozzle) is introduced.",
    ]),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 2. Master picture
# ----------------------------------------------------------------------
story += [
    H1("2. The master picture (keep this in mind)"),
    P("A 1&nbsp;mm nozzle fires hot dense gas into a near-vacuum. The gas:"),
    bullets([
        "<b>Expands</b> at the lip (gets fast and cold).",
        "<b>Over-expands</b> and is pushed back by a <b>barrel shock</b> "
        "(gets hot and slower).",
        "<b>Impinges</b> on a flat plate where it stops axially and turns "
        "radially (stagnation + wall jet).",
        "<b>Delivers</b> pressure, friction, and heat to the plate.",
    ]),
    Q("Every curve you plotted is one snapshot of that story."),
]

# ----------------------------------------------------------------------
# 3. Why each profile looks the way it does
# ----------------------------------------------------------------------
story += [
    H1("3. Why each profile looks the way it does"),

    H2("3.1 Density (&rho;)"),
    P("<b>What it is:</b> mass per unit volume of gas."),
    P("<b>What drives its shape:</b>"),
    bullets([
        "At the nozzle exit, &rho; is highest &mdash; the gas is still "
        "confined.",
        "As the plume moves downstream, it spreads radially into a larger "
        "area, so mass per volume falls.",
        "The expansion wave also reduces density (gas spreading into vacuum).",
        "Orders-of-magnitude drop from nozzle to plate is expected &mdash; "
        "conservation of mass working against geometry.",
        "At large radius, all curves collapse to ambient because the plume no "
        "longer dominates.",
    ]),
    Q("Q&amp;A line: &ldquo;Density drops because the plume is expanding into a "
      "vacuum; the 1&nbsp;mm core spreads into a much larger radial area, and "
      "mass conservation forces &rho; to fall.&rdquo;"),

    H2("3.2 Translational Temperature (T<sub>x</sub>)"),
    P("<b>What it is:</b> the temperature derived from the directed random "
      "motion of molecules in the x-direction. In DSMC it is reported "
      "separately from T<sub>y</sub>, T<sub>z</sub> because they can differ "
      "out of equilibrium."),
    P("<b>What drives its shape:</b>"),
    bullets([
        "<b>Cold dip on the axis:</b> the expansion fan converts thermal "
        "energy into directed kinetic energy &mdash; thermal motion becomes "
        "directed motion, temperature drops.",
        "<b>Temperature peak after the dip:</b> the over-expanded plume is "
        "recompressed across the barrel shock; directed KE is converted back "
        "into random thermal energy, so T jumps.",
        "<b>Relaxation to ambient at large radius:</b> the plume gas mixes "
        "with quiescent ambient.",
        "<b>At the plate (Location&nbsp;1)</b> the curve is nearly flat near "
        "ambient because the wall-jet has mixed and cooled the flow.",
    ]),
    Q("Q&amp;A line: &ldquo;The cold dip is expansion cooling "
      "(thermal &rarr; kinetic), the peak is the barrel-shock recompression "
      "(kinetic &rarr; thermal). Two halves of an under-expanded plume.&rdquo;"),

    H2("3.3 Velocity (U)"),
    P("<b>What it is:</b> the bulk flow speed of the gas."),
    P("<b>What drives its shape:</b>"),
    bullets([
        "<b>High core velocity at Locations&nbsp;3/4/2:</b> the expansion fan "
        "accelerates the gas &mdash; cooling and acceleration are coupled.",
        "<b>Velocity drop after the peak:</b> the barrel shock slows the flow "
        "(compressions always decelerate supersonic flow).",
        "<b>Decay outward from the axis:</b> the plume has less momentum and "
        "more mixing with ambient as r grows.",
        "<b>At the plate, U &asymp; 0 on the axis:</b> the stagnation point; "
        "axial momentum is completely stopped by the plate.",
        "<b>Off-axis on the plate, U rises again:</b> this is the wall-jet, "
        "the axial flow turned 90&deg; to slide along the surface.",
    ]),
    Q("Q&amp;A line: &ldquo;Upper probes show the accelerated jet core from "
      "expansion; the plate profile shows a stagnation point on the axis and "
      "a wall-jet off-axis &mdash; axial momentum is rotated 90&deg; when it "
      "hits the surface.&rdquo;"),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 4. Surface loading
# ----------------------------------------------------------------------
story += [
    H1("4. Surface loading on the plate"),

    H2("4.1 Surface pressure p<sub>wall</sub>"),
    P("<b>What it is:</b> normal force per unit area on the plate."),
    bullets([
        "<b>Maximum at the stagnation point (r=0):</b> axial momentum is "
        "fully destroyed by the plate &mdash; that kinetic energy becomes "
        "stagnation pressure on the surface.",
        "<b>Monotonic decay outward:</b> the radial wall-jet slides along the "
        "surface and exerts almost no normal force.",
        "The shape is roughly a bell curve centered on the axis, with width "
        "comparable to the plume diameter at the plate.",
    ]),
    Q("Q&amp;A line: &ldquo;p<sub>wall</sub> peaks at the stagnation point "
      "because that is where all the axial momentum is destroyed by the "
      "surface, and decays outward because the wall-jet is parallel to the "
      "surface and exerts no normal force.&rdquo;"),

    H2("4.2 Surface shear stress &tau;<sub>wall</sub>"),
    P("<b>What it is:</b> tangential (friction) force per unit area on the "
      "plate &mdash; the force the gas drags along the surface."),
    bullets([
        "<b>Zero at the stagnation point (r=0):</b> by symmetry, there is no "
        "tangential velocity at the axis. No flow along the surface &rArr; "
        "no friction.",
        "<b>Rises to a peak off-axis:</b> where the wall-jet is fully "
        "developed, the near-wall velocity gradient du/dy is maximum, and so "
        "is viscous shear.",
        "<b>Decays outward:</b> the wall-jet slows, its boundary layer "
        "thickens, du/dy falls.",
        "The shape is the characteristic &ldquo;zero&mdash;peak&mdash;decay&rdquo; "
        "curve centered on the stagnation line.",
    ]),
    Q("Q&amp;A line: &ldquo;&tau;<sub>wall</sub> is zero on the axis because "
      "there is no tangential flow at the stagnation point, peaks where the "
      "wall-jet is fastest, and decays as the wall-jet spreads and loses "
      "momentum.&rdquo;"),

    H2("4.3 Heat flux q<sub>wall</sub>"),
    P("<b>What it is:</b> thermal energy per unit area per unit time "
      "transferred from the gas to the plate."),
    P("<b>Why q<sub>wall</sub> peaks at the stagnation point:</b>"),
    bullets([
        "Stagnation gas is at the highest temperature (full kinetic &rarr; "
        "thermal conversion at the impact point).",
        "The thermal boundary layer is thinnest there, so dT/dy is largest.",
        "Density is also highest &mdash; more molecules hit the wall per "
        "second.",
    ]),
    P("<b>Decays outward:</b> the wall-jet cools, boundary layer thickens, "
      "density falls &mdash; all three reduce dT/dy and therefore q<sub>wall</sub>."),
    P("<b>In DSMC you also multiply by the thermal accommodation coefficient "
      "&alpha;</b>: molecules do not always fully exchange energy with the "
      "wall in a single collision, which is why rarefied q<sub>wall</sub> "
      "peaks are lower than continuum predictions."),
    Q("Q&amp;A line: &ldquo;q<sub>wall</sub> peaks at the stagnation point where "
      "the gas is hottest, the boundary layer is thinnest, and density is "
      "highest; it decays outward for the same reasons. For rarefied flow "
      "the peak is scaled by the thermal accommodation coefficient.&rdquo;"),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 5. Expansion wave vs barrel shock
# ----------------------------------------------------------------------
story += [
    H1("5. Expansion wave vs barrel shock"),
    P("They are <b>two different things</b>, and <b>both are in your plume</b>. "
      "They just occur at different stages of the same flow."),
]

diff_rows = [
    ["Aspect", "Expansion wave (Prandtl&ndash;Meyer fan)", "Barrel shock"],
    ["Nature",
     "Smooth, isentropic (reversible)",
     "Shock &mdash; discontinuous, non-isentropic (irreversible)"],
    ["Effect on gas",
     "Accelerates, cools, density drops",
     "Decelerates/redirects, heats, density rises"],
    ["Location",
     "At the nozzle lip and through the near-field core",
     "Curved shock wrapping the plume boundary, further downstream"],
    ["Signature in your plots",
     "Cold spot / density drop on the axis at Locs&nbsp;3/4/2",
     "T<sub>x</sub> peak after the cold spot, density recovery, U drop"],
]
diff_tbl = []
for i, row in enumerate(diff_rows):
    diff_tbl.append([Paragraph(cell, styles["Body"]) for cell in row])
story.append(make_table(diff_tbl, col_widths=[3.4 * cm, 6.0 * cm, 6.6 * cm]))

story += [
    Spacer(1, 0.4 * cm),
    H2("The sequence in an under-expanded nozzle plume"),
    bullets([
        "<b>Nozzle lip:</b> p<sub>nozzle</sub> &gt;&gt; p<sub>ambient</sub>. "
        "Prandtl&ndash;Meyer fan fires radially outward; core gas turns, "
        "accelerates, cools.",
        "<b>Jet boundary:</b> the expansion fan reflects off the "
        "constant-pressure contact surface and returns as compression.",
        "<b>Compression coalesces into a shock</b> &rarr; the barrel shock. "
        "Gas crossing it is compressed, heated, slowed.",
        "<b>Mach disk (optional):</b> if pressure ratio is high enough, the "
        "barrel shock terminates in a normal shock on the axis.",
        "Post-shock gas then impinges on the plate.",
    ]),
    Q("&ldquo;The expansion fan and the barrel shock are not the same &mdash; "
      "they are the two halves of the same story. The expansion fan cools "
      "and accelerates the core (cold spot), and the barrel shock recompresses "
      "it (temperature peak). Both have to be present in an under-expanded "
      "plume &mdash; if only one were, mass and momentum would not balance.&rdquo;"),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 6. Is it a barrel shock? How do I know?
# ----------------------------------------------------------------------
story += [
    H1("6. How do we know it really is a barrel shock?"),
    P("Three pieces of evidence, all of which must be true for a barrel shock. "
      "This simulation satisfies all three."),

    H2("Evidence 1 &mdash; Geometry forces under-expansion"),
    P("A 1&nbsp;mm nozzle firing into a near-vacuum ambient is automatically "
      "under-expanded. That guarantees an expansion fan at the lip and a "
      "recompression shock downstream &mdash; it is not a guess, it is a "
      "conservation requirement."),

    H2("Evidence 2 &mdash; The T<sub>x</sub> profile has the canonical "
       "dip-then-peak signature"),
    P("In <font face='Courier'>trans112.png</font>, Locations&nbsp;3/4/2 show:"),
    bullets([
        "A cold minimum near the axis &rarr; expansion fan (isentropic cooling).",
        "A broad hot peak off-axis &rarr; gas crossing a recompression shock.",
    ]),
    P("A free, unshocked plume would show only the cold core monotonically "
      "relaxing to ambient. The presence of a peak is the fingerprint of a "
      "shock wave, and the fact that the peak lies <b>off the axis</b> tells "
      "you it is an oblique/curved shock wall, not a normal shock on axis."),

    H2("Evidence 3 &mdash; The peak moves radially with axial distance"),
    P("The radial position of the T<sub>x</sub> peak at Locations&nbsp;3, 4, 2 "
      "is different at different heights. A planar shock would show the peak "
      "at the same radius at every height. A peak that migrates radially with "
      "height is a <b>curved shock</b> &mdash; exactly what a barrel shock is."),

    H2("Cross-check from the other two plots"),
    bullets([
        "<b>den112:</b> density collapses through the expansion fan and shows "
        "a small local recovery at the same radial position where T<sub>x</sub> "
        "peaks &rArr; consistent with a compressive shock.",
        "<b>velocity112:</b> velocity drops sharply at the same radial location "
        "&rArr; consistent with a shock, which must decelerate supersonic flow.",
    ]),

    H2("Ruling out the alternatives"),
]

alt_rows = [
    ["Alternative", "Would look like", "Why ruled out"],
    ["No shock (pure expansion)",
     "Monotonic cold core relaxing to ambient",
     "We see a temperature peak"],
    ["Mach disk (normal shock on axis)",
     "T peak on the axis (r=0)",
     "Our peaks are off the axis"],
    ["Bow shock from the plate",
     "Peak just above the plate at Location&nbsp;1 only",
     "Our peaks are at Locs&nbsp;3/4/2 upstream; Loc&nbsp;1 is nearly flat"],
    ["Contact-surface mixing only",
     "Gradual blending, no sharp peak",
     "We have a sharp peak, not gradual mixing"],
]
alt_tbl = [[Paragraph(c, styles["Body"]) for c in row] for row in alt_rows]
story.append(make_table(alt_tbl, col_widths=[4.0 * cm, 6.0 * cm, 6.0 * cm]))

story += [
    Spacer(1, 0.4 * cm),
    Q("&ldquo;A barrel shock is the curved oblique recompression shock that "
      "wraps around the core of an under-expanded plume. I'm sure mine is a "
      "barrel shock because (a) a 1&nbsp;mm nozzle into vacuum is automatically "
      "under-expanded so a recompression shock is required, (b) the T<sub>x</sub>, "
      "density and velocity profiles show a sharp off-axis jump &mdash; the "
      "signature of a shock, not of free mixing, and (c) the radial position of "
      "that jump moves with axial height, which means the shock wall is curved. "
      "Planar result would be a Mach disk; off-axis, height-dependent result is "
      "a barrel shock.&rdquo;"),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 7. Wall jet explained
# ----------------------------------------------------------------------
story += [
    H1("7. What a wall jet is, and how it develops"),
    P("<b>Definition:</b> a wall jet is the thin, fast-moving layer of gas "
      "that flows parallel to a surface after an impinging jet has been turned "
      "by that surface."),
    Q("&ldquo;A wall jet is the radial stream of fluid that forms after an axial "
      "jet impinges on a surface, because the jet's axial momentum cannot pass "
      "through the wall and is redirected sideways along it.&rdquo;"),

    H2("Development &mdash; the four stages"),
    bullets([
        "<b>Stage 1 &mdash; Free jet approach:</b> the jet is still moving "
        "axially, nothing special at the wall yet.",
        "<b>Stage 2 &mdash; Stagnation region (r&nbsp;&asymp;&nbsp;0):</b> the "
        "plate blocks axial motion; flow decelerates to zero on the axis. "
        "Axial momentum becomes high surface pressure and a radial pressure "
        "gradient.",
        "<b>Stage 3 &mdash; Turning region (within ~1 jet diameter):</b> the "
        "radial pressure gradient accelerates the fluid outward; the flow is "
        "turned 90&deg; from axial to radial. By the end of the turning region, "
        "the jet is a thin sheet flowing radially along the plate &mdash; the "
        "wall jet.",
        "<b>Stage 4 &mdash; Wall-jet region (beyond ~1 jet diameter):</b> the "
        "jet has its characteristic two-layer structure.",
    ]),

    H2("Two stacked layers of the wall-jet"),
    bullets([
        "<b>Inner layer (wall &rarr; velocity peak):</b> a classical viscous "
        "boundary layer; velocity zero at the wall, rises to a maximum a "
        "short distance above. Shear stress and heat flux are high here "
        "because the gradients of u and T are steepest.",
        "<b>Outer layer (velocity peak &rarr; ambient):</b> a free shear "
        "layer that mixes with and entrains the ambient gas above.",
    ]),

    H2("Why it exists (two conservation laws)"),
    bullets([
        "<b>Mass conservation:</b> mass arrives continuously at the "
        "stagnation region, cannot accumulate (steady state) and cannot go "
        "through the plate; the only escape is along the plate.",
        "<b>Momentum conservation:</b> incoming axial momentum has to go "
        "somewhere. Part becomes normal force on the plate, the rest is "
        "rotated into the radial direction and carried away by the wall jet.",
    ]),

    H2("Why it matters for PSI"),
]

wj_rows = [
    ["Quantity", "Peaks where", "Why"],
    ["p<sub>wall</sub>",
     "Stagnation point (r=0)",
     "Full axial momentum destroyed there"],
    ["&tau;<sub>wall</sub>",
     "Off-axis, inside the wall-jet region",
     "du/dy is steepest where the wall-jet is fully established"],
    ["q<sub>wall</sub>",
     "Stagnation point (r=0)",
     "Thinnest thermal boundary layer + hottest stagnation gas"],
]
wj_tbl = [[Paragraph(c, styles["Body"]) for c in row] for row in wj_rows]
story.append(make_table(wj_tbl, col_widths=[3.0 * cm, 5.0 * cm, 8.0 * cm]))

story += [
    Spacer(1, 0.4 * cm),
    Q("&ldquo;A wall jet is the thin radial layer that forms along the plate "
      "after the plume impinges, because mass and momentum have no other "
      "escape route than to turn and flow along the surface. It has an inner "
      "viscous boundary layer plus an outer free-shear layer, and it is what "
      "sets the distribution of shear and heat flux on the plate away from "
      "the stagnation point.&rdquo;"),
]

story.append(PageBreak())

# ----------------------------------------------------------------------
# 8. The single defensible sentence
# ----------------------------------------------------------------------
story += [
    H1("8. The single sentence that ties everything together"),
    Q("&ldquo;Density falls because the plume expands into vacuum. Temperature "
      "first falls (expansion cooling) then rises (barrel shock recompression) "
      "then relaxes to ambient. Velocity accelerates through the expansion fan, "
      "slows across the shock, and goes to zero on the plate axis where it "
      "turns into a radial wall-jet. That stagnation point is where the plate "
      "gets the most pressure and the most heat; the wall-jet off-axis is "
      "where it gets the most shear. Every curve on every plot is one of "
      "those four stages &mdash; expansion &rarr; shock &rarr; stagnation "
      "&rarr; wall-jet.&rdquo;"),
    Spacer(1, 0.5 * cm),
    H2("Q&amp;A escape hatch"),
    P("If someone asks &ldquo;why does your curve look like X?&rdquo; and you "
      "are not sure, fall back to:"),
    Q("&ldquo;That follows from the chain: expansion &rarr; shock recompression "
      "&rarr; stagnation &rarr; wall-jet. Whichever of those four stages "
      "dominates at that probe location sets the local &rho;/T/U, and whichever "
      "of the stagnation vs. wall-jet region dominates at that radius sets the "
      "local p<sub>wall</sub>/&tau;<sub>wall</sub>/q<sub>wall</sub>.&rdquo;"),
    P("That answer is physically correct for every point on every one of your "
      "curves, so you cannot be cornered."),
]


def footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 8)
    canv.setFillColor(colors.HexColor("#666666"))
    canv.drawString(2 * cm, 1.2 * cm,
                    "PSI physics notes  |  1 mm nozzle plume on flat surface")
    canv.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"page {doc.page}")
    canv.restoreState()


doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2.0 * cm, rightMargin=2.0 * cm,
    topMargin=2.0 * cm, bottomMargin=2.0 * cm,
    title="PSI physics notes",
    author="Fahim Shahriyar",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"[ok] wrote {OUT}")
