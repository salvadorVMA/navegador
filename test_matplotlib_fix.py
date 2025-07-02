#!/usr/bin/env python3
"""
Quick test to verify matplotlib Agg backend is working correctly
"""

# Set backend before importing any matplotlib components
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

print("Testing matplotlib with Agg backend...")

# Create sample data
data = {'Category A': 25.5, 'Category B': 30.2, 'Category C': 18.7, 'Category D': 25.6}
df = pd.DataFrame(list(data.items()), columns=['Category', 'Value'])
df.set_index('Category', inplace=True)

# Test horizontal bar plot
fig, ax = plt.subplots(figsize=(6, 4))
y_pos = np.arange(len(df))
values = np.array(df['Value'].values, dtype=float)
labels = df.index.tolist()

bars = ax.barh(y_pos, values, color='skyblue', edgecolor='black', linewidth=0.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xlabel('Percentage (%)', fontsize=9)
ax.set_title('Test Plot with Agg Backend', fontsize=10, fontweight='bold')

# Save the plot
plt.tight_layout()
plt.savefig('test_plot.png', dpi=150, bbox_inches='tight')
plt.close()

print("✅ Test plot saved successfully as 'test_plot.png'")
print("✅ matplotlib Agg backend is working correctly!")
