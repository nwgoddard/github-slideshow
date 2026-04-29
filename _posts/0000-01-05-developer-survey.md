---
layout: slide
title: "Developer Survey — Financing Terms"
slide-id: developer-survey
---

<p style="color:#aaa; font-size:0.85rem; margin-bottom:1rem;">
  Source: RealtyRates.com Developer Survey &nbsp;·&nbsp;
  {{ site.data.realtyrates.developer_survey.quarter }}
</p>

{% for cat in site.data.realtyrates.developer_survey.categories %}
<div style="margin-bottom:1.2rem;">
  <h3 style="font-size:1rem; color:#4f8ef7; margin-bottom:0.4rem;">{{ cat.name }}</h3>
  <table style="width:100%; border-collapse:collapse; font-size:0.8rem;">
    <thead>
      <tr style="border-bottom:1px solid #444;">
        <th style="text-align:left; padding:0.3rem 0.5rem; color:#777;">Metric</th>
        <th style="text-align:right; padding:0.3rem 0.5rem; color:#777;">Low</th>
        <th style="text-align:right; padding:0.3rem 0.5rem; color:#777;">High</th>
        <th style="text-align:right; padding:0.3rem 0.5rem; color:#777;">Avg</th>
      </tr>
    </thead>
    <tbody>
      {% for m in cat.metrics %}
      <tr style="border-bottom:1px solid #2a2d3a;">
        <td style="padding:0.3rem 0.5rem;">{{ m.name }}</td>
        <td style="text-align:right; padding:0.3rem 0.5rem; color:#888;">{{ m.low }} {{ m.unit }}</td>
        <td style="text-align:right; padding:0.3rem 0.5rem; color:#888;">{{ m.high }} {{ m.unit }}</td>
        <td style="text-align:right; padding:0.3rem 0.5rem; color:#4caf7d; font-weight:600;">{{ m.avg }} {{ m.unit }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endfor %}
