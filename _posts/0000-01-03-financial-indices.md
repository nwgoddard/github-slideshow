---
layout: slide
title: "Financial Benchmark Rates"
slide-id: financial-indices
---

<p style="color:#aaa; font-size:0.85rem; margin-bottom:1.2rem;">
  Source: RealtyRates.com Financial Indices &nbsp;·&nbsp;
  {{ site.data.realtyrates.metadata.last_updated | date: "%B %Y" }}
</p>

<table style="width:100%; border-collapse:collapse; font-size:0.88rem;">
  <thead>
    <tr style="border-bottom:1px solid #444;">
      <th style="text-align:left; padding:0.5rem 0.75rem; color:#888;">Index</th>
      <th style="text-align:right; padding:0.5rem 0.75rem; color:#888;">Rate</th>
      <th style="text-align:left; padding:0.5rem 0.75rem; color:#888;">Category</th>
    </tr>
  </thead>
  <tbody>
    {% for idx in site.data.realtyrates.indices.indices %}
    <tr style="border-bottom:1px solid #333;">
      <td style="padding:0.5rem 0.75rem;">{{ idx.name }}</td>
      <td style="text-align:right; padding:0.5rem 0.75rem; color:#4f8ef7; font-weight:600;">
        {{ idx.value }}%
      </td>
      <td style="padding:0.5rem 0.75rem; color:#888; font-size:0.8rem;">{{ idx.category }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<p style="color:#666; font-size:0.78rem; margin-top:1rem;">
  Benchmark rates directly impact subdivision land loan and construction loan pricing.
</p>
