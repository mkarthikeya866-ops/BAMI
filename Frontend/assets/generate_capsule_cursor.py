import math
import os
from PIL import Image, ImageDraw, ImageFilter

def create_capsule_cursor():
    assets_dir = "/Users/m.saikarthikeya/Desktop/XGBioactiveNew/Frontend/assets"
    os.makedirs(assets_dir, exist_ok=True)
    png_path = os.path.join(assets_dir, "capsule-cursor.png")
    svg_path = os.path.join(assets_dir, "capsule-cursor.svg")

    # -------------------------------------------------------------
    # 1. GENERATE SVG VERSION (Crisp Vector)
    # -------------------------------------------------------------
    # In 32x32 viewbox:
    # Capsule oriented at -45 deg (pointing to top-left).
    # Unrotated capsule: centered at (0, 0), width = 8.5, height = 23, rx = 4.25
    # Hotspot is at top tip.
    # Center placed at (14.5, 14.5).
    # Unrotated top tip is at (0, -11.5).
    # Rotated -45 deg: (-11.5 * -sin(-45), -11.5 * cos(-45)) = (-11.5 * 0.7071, -11.5 * 0.7071)
    # dx = -8.13, dy = -8.13.
    # Top tip at 14.5 - 8.13 = 6.37.
    # If we shift center to (12.5, 12.5): top tip at 12.5 - 8.13 = 4.37 ≈ 4px.
    # Hotspot = (4, 4).
    # Bottom tip at 12.5 + 8.13 = 20.63 ≈ 21px.

    cx, cy = 12.5, 12.5
    w_cap = 8.2
    h_cap = 22.0
    r_cap = w_cap / 2.0 # 4.1

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <defs>
    <!-- Soft Drop Shadow Filter -->
    <filter id="cursor-shadow" x="-30%" y="-30%" width="170%" height="170%">
      <feDropShadow dx="1" dy="1.5" stdDeviation="1.2" flood-color="#1E142F" flood-opacity="0.45" />
    </filter>

    <!-- Top Cap (Deep Lavender/Purple) Gradient -->
    <linearGradient id="purple-half" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#937DC2" />
      <stop offset="45%" stop-color="#7562A2" />
      <stop offset="100%" stop-color="#55427D" />
    </linearGradient>

    <!-- Bottom Cap (Soft Lilac / White) Gradient -->
    <linearGradient id="white-half" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="55%" stop-color="#EDE7F7" />
      <stop offset="100%" stop-color="#D4C8EB" />
    </linearGradient>

    <!-- 3D Specular Sheen Gradient -->
    <linearGradient id="capsule-sheen" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.75" />
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>

    <!-- Capsule Clip Path for 2 Halves -->
    <clipPath id="capsule-shape">
      <rect x="{-w_cap/2}" y="{-h_cap/2}" width="{w_cap}" height="{h_cap}" rx="{r_cap}" ry="{r_cap}" />
    </clipPath>
  </defs>

  <!-- Transform to angle -45 deg, centered at ({cx}, {cy}) -->
  <g transform="translate({cx}, {cy}) rotate(-45)" filter="url(#cursor-shadow)">
    <!-- Main Capsule Container clipped to rounded pill -->
    <g clip-path="url(#capsule-shape)">
      <!-- Top Half (Purple) -->
      <rect x="{-w_cap/2}" y="{-h_cap/2}" width="{w_cap}" height="{h_cap/2 + 0.2}" fill="url(#purple-half)" />

      <!-- Bottom Half (Soft White/Lilac) -->
      <rect x="{-w_cap/2}" y="0" width="{w_cap}" height="{h_cap/2 + 0.2}" fill="url(#white-half)" />

      <!-- Center Joint Band -->
      <line x1="{-w_cap/2}" y1="0" x2="{w_cap/2}" y2="0" stroke="#37264F" stroke-width="0.85" />
      <line x1="{-w_cap/2}" y1="0.85" x2="{w_cap/2}" y2="0.85" stroke="#FFFFFF" stroke-opacity="0.5" stroke-width="0.4" />

      <!-- Specular Highlight Strip along left edge -->
      <path d="M {-w_cap/2 + 0.8} {-h_cap/2 + 3} Q {-w_cap/2 + 0.8} 0 {-w_cap/2 + 0.8} {h_cap/2 - 3}"
            stroke="url(#capsule-sheen)" stroke-width="1.2" stroke-linecap="round" fill="none" />
    </g>

    <!-- Crisp Pill Border -->
    <rect x="{-w_cap/2}" y="{-h_cap/2}" width="{w_cap}" height="{h_cap}" rx="{r_cap}" ry="{r_cap}"
          fill="none" stroke="#251B35" stroke-width="0.9" />

    <!-- Tiny Pinpoint Pointer Indicator at Top Tip -->
    <circle cx="0" cy="{-h_cap/2 + 0.4}" r="0.6" fill="#FFFFFF" opacity="0.9" />
  </g>
</svg>
'''

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"[OK] Saved SVG cursor to {svg_path}")

    # -------------------------------------------------------------
    # 2. GENERATE SUPERSAMPLED 32x32 PNG
    # -------------------------------------------------------------
    # 8x supersampling for high fidelity antialiasing
    scale = 8
    canvas_size = 32 * scale  # 256
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))

    # We will draw a supersampled pill on a separate high-res canvas
    # Center = (cx * scale, cy * scale) = (100, 100)
    SCX = cx * scale
    SCY = cy * scale
    SW = w_cap * scale
    SH = h_cap * scale
    SR = r_cap * scale

    # Create unrotated pill canvas
    pill_img = Image.new("RGBA", (int(SW + 16), int(SH + 16)), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(pill_img)

    offset_x = 8
    offset_y = 8
    x0 = offset_x
    y0 = offset_y
    x1 = offset_x + SW
    y1 = offset_y + SH

    # Draw rounded rectangle mask
    # Top half (purple)
    # We can draw the whole pill with purple, then bottom half with white
    # Draw bottom rounded cap + rectangle
    pdraw.rounded_rectangle([x0, y0, x1, y1], radius=SR, fill=(117, 98, 162, 255))

    # Draw top gradient or colors
    for y in range(int(y0), int(y0 + SH / 2)):
        ratio = (y - y0) / (SH / 2)
        r = int(147 * (1 - ratio) + 95 * ratio)
        g = int(125 * (1 - ratio) + 74 * ratio)
        b = int(194 * (1 - ratio) + 135 * ratio)
        # only fill inside the rounded shape
        # Let's use mask to be exact
        pass

    # Better approach: Draw on high-res PIL Image using math:
    # For every pixel in high-res canvas, compute distance to capsule segments!
    hi_res = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    pixels = hi_res.load()

    # Capsule segment:
    # Axis is along angle -45 deg from positive X (pointing up-left):
    # Unit vector towards top tip: u = (-sqrt(0.5), -sqrt(0.5))
    # Unit vector perpendicular: v = (sqrt(0.5), -sqrt(0.5))
    cos45 = math.cos(math.radians(45))
    sin45 = math.sin(math.radians(45))

    half_cyl = (SH - SW) / 2.0  # length of straight cylinder part on each side of center

    # Center of capsule in 256px
    center_x = SCX
    center_y = SCY

    # Shadow buffer
    shadow_img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    shadow_pix = shadow_img.load()

    for py in range(canvas_size):
        for px in range(canvas_size):
            # Coordinates relative to center
            dx = px - center_x
            dy = py - center_y

            # Project onto axis (u points up-left towards tip: -dx*cos45 - dy*sin45)
            # axial distance from center: positive = top-left (purple), negative = bottom-right (white)
            axial = - (dx + dy) * cos45
            # lateral distance from axis
            lateral = abs((dx - dy) * cos45)

            # Distance to central segment of length 2 * half_cyl
            clamped_axial = max(-half_cyl, min(half_cyl, axial))
            dist_to_segment = math.hypot(axial - clamped_axial, lateral)

            # Capsule boundary
            edge_dist = dist_to_segment - SR

            if edge_dist <= 2.0:
                # Inside or on anti-aliased edge
                alpha = max(0.0, min(1.0, 0.5 - edge_dist * 0.5))
                if alpha <= 0.01:
                    continue

                # Check if outline (outer 1.1px * scale = 8.8px)
                border_width = 1.0 * scale
                is_border = (SR - dist_to_segment) < border_width

                if is_border:
                    # Dark purple border #251B35
                    col_r, col_g, col_b = 37, 27, 53
                elif abs(axial) < (0.6 * scale):
                    # Center dividing band
                    col_r, col_g, col_b = 55, 38, 79
                elif axial > 0:
                    # Top-left half: Purple (#7562A2 to #5A4482)
                    t = (axial - 0) / (half_cyl + SR)
                    col_r = int(147 - t * 45)
                    col_g = int(125 - t * 45)
                    col_b = int(194 - t * 50)
                else:
                    # Bottom-right half: Soft Lilac/White (#FFFFFF to #D4C8EB)
                    t = (-axial) / (half_cyl + SR)
                    col_r = int(255 - t * 35)
                    col_g = int(255 - t * 42)
                    col_b = int(255 - t * 25)

                # Specular sheen on top edge (lateral close to SR on upper side: dx - dy < 0)
                if (dx - dy) * cos45 < - (SR * 0.2) and (dx - dy) * cos45 > - (SR * 0.85) and not is_border:
                    sheen = max(0.0, 1.0 - abs(((dx - dy) * cos45) + (SR * 0.55)) / (SR * 0.35)) * 0.45
                    col_r = int(col_r + (255 - col_r) * sheen)
                    col_g = int(col_g + (255 - col_g) * sheen)
                    col_b = int(col_b + (255 - col_b) * sheen)

                pixels[px, py] = (col_r, col_g, col_b, int(alpha * 255))

            # Shadow pass
            s_dx = px - (center_x + 1.2 * scale)
            s_dy = py - (center_y + 1.6 * scale)
            s_axial = - (s_dx + s_dy) * cos45
            s_lateral = abs((s_dx - s_dy) * cos45)
            s_clamped = max(-half_cyl, min(half_cyl, s_axial))
            s_dist = math.hypot(s_axial - s_clamped, s_lateral)
            s_edge = s_dist - (SR + 0.5 * scale)
            if s_edge < 3.0 * scale:
                s_alpha = max(0.0, min(0.38, (1.0 - s_edge / (3.0 * scale)) * 0.38))
                shadow_pix[px, py] = (25, 15, 38, int(s_alpha * 255))

    # Composite shadow behind capsule
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=1.5 * scale))
    final_img = Image.alpha_composite(shadow_img, hi_res)

    # Downscale to 32x32 using high quality Lanczos filter
    final_32 = final_img.resize((32, 32), Image.Resampling.LANCZOS)
    final_32.save(png_path, "PNG")
    print(f"[OK] Saved 32x32 transparent PNG cursor to {png_path}")

create_capsule_cursor()
