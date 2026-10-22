"""Figure 2: three illustrative shapes of the review-effort curve (assumed values, not results).

Usage: python figures/figure2_review_effort_curves.py [output.png]
"""
import sys
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os
_fonts = [f'/usr/share/fonts/truetype/crosextra/Carlito-{s}.ttf' for s in ('Regular', 'Bold', 'Italic')]
_family = 'DejaVu Sans'
if all(os.path.exists(f) for f in _fonts):
    for f in _fonts:
        fm.fontManager.addfont(f)
    _family = 'Carlito'
plt.rcParams.update({'font.family': _family, 'font.size': 9.5, 'axes.linewidth': 0.8,
                     'axes.edgecolor': '#8a8985', 'xtick.color': '#52514e', 'ytick.color': '#52514e'})

# Illustrative assumptions, not results
A0, H, T = 82.0, 97.0, 90.0   # agreement without review, human-human agreement (ceiling), target (Lombard et al., 2002)
x = np.linspace(0, 1, 1001)
early = A0 + (H - A0) * (1 - (1 - x) ** 3.2)
linear = A0 + (H - A0) * x
sig = lambda z: 1 / (1 + np.exp(-z))
m, s = 0.62, 0.065
late = A0 + (H - A0) * (sig((x - m) / s) - sig((0 - m) / s)) / (sig((1 - m) / s) - sig((0 - m) / s))


def cross(y):
    return x[np.argmax(y >= T)] * 100


ink, ink2, muted = '#0b0b0b', '#52514e', '#8a8985'
c_early, c_lin, c_late = '#00A86B', '#6b6a66', '#E0201B'

fig, ax = plt.subplots(figsize=(6.3, 4.35), dpi=300)
ax.grid(True, color='#e9e8e4', linewidth=0.6)
ax.set_axisbelow(True)
for side in ['top', 'right']:
    ax.spines[side].set_visible(False)

# target line
ax.axhline(T, color=ink2, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
ax.text(99.0, T - 0.3, 'Target: 90% agreement\n(Lombard et al., 2002)', ha='right', va='top', linespacing=1.15,
        color=ink2, fontsize=8.5)

# curves
ax.plot(x * 100, linear, color=c_lin, linewidth=1.8, linestyle=(0, (5, 2.5)), zorder=3)
ax.plot(x * 100, late, color=c_late, linewidth=2.0, linestyle=(0, (7, 2, 1.5, 2)), zorder=3)
ax.plot(x * 100, early, color=c_early, linewidth=2.0, zorder=4)

# review share needed to reach target
for y, c in [(early, c_early), (late, c_late), (linear, c_lin)]:
    xc = cross(y)
    ax.plot([xc, xc], [79.5, T], color=c, linewidth=0.8, linestyle=(0, (1, 2)), zorder=2)
    ax.plot([xc], [T], marker='o', markersize=5.5, markerfacecolor=c, markeredgecolor='white',
            markeredgewidth=1.2, zorder=5)
    ax.text(xc, 79.85, f'{xc:.0f}%', ha='center', va='bottom', color=ink, fontsize=8.5,
            bbox=dict(boxstyle='square,pad=0.15', fc='white', ec='none'), zorder=6)

ax.text(18.8, 79.85, 'Review needed:', ha='right', va='bottom', color=ink2, fontsize=8)
# direct labels (short) + legend with explanations below the plot
ax.text(30.0, 93.4, 'Early flattening', color=c_early, fontsize=9.5, fontweight='bold', ha='right')
ax.text(25.5, 87.35, 'Linear', color=c_lin, fontsize=9.5, fontweight='bold', ha='left')
ax.text(29.5, 83.0, 'Late jump', color=c_late, fontsize=9.5, fontweight='bold', ha='left')

ax.annotate('No review: model only', xy=(0.4, A0), xytext=(3.0, 81.3), fontsize=8, color=ink2,
            va='center', arrowprops=dict(arrowstyle='-', color=muted, linewidth=0.7))
ax.annotate('Full review: agreement between two human coders', xy=(99.6, H), xytext=(90, 98.2), fontsize=8,
            color=ink2, ha='right', va='center',
            arrowprops=dict(arrowstyle='-', color=muted, linewidth=0.7))

from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=c_early, lw=2.0),
           Line2D([0], [0], color=c_lin, lw=1.8, linestyle=(0, (5, 2.5))),
           Line2D([0], [0], color=c_late, lw=2.0, linestyle=(0, (7, 2, 1.5, 2)))]
labels = ['Early flattening: errors cluster in low-confidence segments, so confidence-based routing pays off',
          'Linear: confidence carries no signal about errors, so review is no better than a random sample',
          'Late jump: review first hits correct segments, and gains start once it reaches a class of confident errors']
leg = fig.legend(handles, labels, loc='lower left', bbox_to_anchor=(0.085, 0.0), ncol=1, frameon=False,
                 fontsize=8.3, handlelength=3.2, labelcolor=ink2, borderaxespad=0.2)

ax.set_xlim(0, 100)
ax.set_ylim(79.5, 98.7)
ax.set_xticks(range(0, 101, 10))
ax.set_yticks([80, 82, 84, 86, 88, 90, 92, 94, 96, 98])
ax.set_xlabel('Share of segments reviewed by researchers, lowest model confidence first (%)', color=ink2)
ax.set_ylabel('Percent agreement with the reference coding (%)', color=ink2)
ax.tick_params(length=0, labelsize=8.5)
fig.tight_layout(pad=0.4, rect=(0, 0.15, 1, 1))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figure2_review_effort_curves.png')
fig.savefig(out, dpi=300, facecolor='white')
print('crossings', round(cross(early), 1), round(cross(late), 1), round(cross(linear), 1))
