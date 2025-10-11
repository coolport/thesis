import pandas as pd
import numpy as np

HTML_TEMPLATE = """ 
<html>
<head>
<style>
  body {{{{ font-family: sans-serif; }}}}
  .tg  {{ border-collapse:collapse; border-spacing:0; }}
  .tg td{{ border-color:black; border-style:solid; border-width:1px; padding:10px 5px; overflow:hidden; word-break:normal; }}
  .tg th{{ border-color:black; border-style:solid; border-width:1px; font-weight:normal; padding:10px 5px; overflow:hidden; word-break:normal; }}
  .tg .tg-0lax{{ text-align:left; vertical-align:top }}
</style>
</head>
<body>
{content}
</body>
</html>
"""

def main(output_file):
    """Reads the results.csv file, performs all analyses, and generates an HTML report."""
    try:
        df = pd.read_csv('results.csv')
        df = df.set_index('agent_type')
    except FileNotFoundError:
        print("Error: results.csv not found. Please run the evaluation experiments first.")
        return

    metrics = {
        'avg_wait_time': 'min',
        'avg_queue_length': 'min',
        'total_throughput': 'max',
        'total_reward': 'max'
    }
    ranks = pd.DataFrame(index=df.index)

    for metric, goal in metrics.items():
        min_val = df[metric].min()
        max_val = df[metric].max()
        
        # Avoid division by zero if all values are the same
        if min_val == max_val:
            ranks[f'{metric}_rank'] = 10.0
            df[f'{metric}_%diff'] = 0.0
            continue

        if goal == 'min':
            # For minimization, lower is better.
            ranks[f'{metric}_rank'] = 10 * (max_val - df[metric]) / (max_val - min_val)
            best_value = min_val
            percent_diff = (df[metric] - best_value) / abs(best_value) if best_value != 0 else 0
        else: # max
            # For maximization, higher is better.
            ranks[f'{metric}_rank'] = 10 * (df[metric] - min_val) / (max_val - min_val)
            best_value = max_val
            percent_diff = (best_value - df[metric]) / abs(best_value) if best_value != 0 else 0
        
        df[f'{metric}_%diff'] = percent_diff

    df = df.round(2)
    ranks = ranks.round(2)

    trials = {
        "Trial 1: Balanced": {'avg_wait_time': 0.25, 'avg_queue_length': 0.25, 'total_throughput': 0.25, 'total_reward': 0.25},
        "Trial 2: Prioritize Flow": {'avg_wait_time': 0.10, 'avg_queue_length': 0.10, 'total_throughput': 0.70, 'total_reward': 0.10},
        "Trial 3: Prioritize Wait Time": {'avg_wait_time': 0.70, 'avg_queue_length': 0.10, 'total_throughput': 0.10, 'total_reward': 0.10},
    }
    sensitivity_results = pd.DataFrame(index=df.index)

    for trial_name, weights in trials.items():
        for agent in df.index:
            total_score = 0
            for metric in metrics:
                total_score += ranks.loc[agent, f'{metric}_rank'] * weights[metric]
            sensitivity_results.loc[agent, trial_name] = total_score

    sensitivity_results = sensitivity_results.round(2)

    # --- Generate HTML Content ---
    content = '<h1>Multiple Constraints and Tradeoff Analysis</h1>'
    
    content += '<h3>Raw Performance Data</h3>'
    content += df[[col for col in df.columns if '%' not in col]].to_html(border=1, classes="tg")

    content += '<h3>Subordinate Rank Calculation (Criterion Scores)</h3>'
    content += ranks.to_html(border=1, classes="tg")

    content += '<h2>Trade-off Analysis Tables</h2>'
    table_df_wait = pd.DataFrame({
        'Controller': df.index,
        'Average Wait Time (s)': df['avg_wait_time'],
        '% Difference': (df['avg_wait_time_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['avg_wait_time_rank']
    }).reset_index(drop=True)
    content += '<h3>Table X - Average Wait Time Comparison (Lower is Better)</h3>'
    content += table_df_wait.to_html(index=False, border=1, classes="tg")

    table_df_queue = pd.DataFrame({
        'Controller': df.index,
        'Average Queue Length': df['avg_queue_length'],
        '% Difference': (df['avg_queue_length_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['avg_queue_length_rank']
    }).reset_index(drop=True)
    content += '<h3>Table Y - Average Queue Length Comparison (Lower is Better)</h3>'
    content += table_df_queue.to_html(index=False, border=1, classes="tg")

    table_df_throughput = pd.DataFrame({
        'Controller': df.index,
        'Total Throughput': df['total_throughput'],
        '% Difference': (df['total_throughput_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['total_throughput_rank']
    }).reset_index(drop=True)
    content += '<h3>Table Z - Total Throughput Comparison (Higher is Better)</h3>'
    content += table_df_throughput.to_html(index=False, border=1, classes="tg")

    content += '<h2>Sensitivity Analysis Tables</h2>'
    for trial_name, weights in trials.items():
        controllers = df.index.tolist()
        num_controllers = len(controllers)
        table_html = f'<h3>{trial_name}</h3>'
        table_html += '<table style="border-collapse:collapse;border-spacing:0" class="tg"><thead>'
        table_html += '<tr><th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top" rowspan="3">Criteria</th>'
        table_html += '<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top" rowspan="3">Criterion Weight (CW)</th>'
        table_html += f'<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:center;vertical-align:top" colspan="{num_controllers * 2}">Algorithm Weighted Score</th></tr>'
        table_html += '<tr>'
        for agent in controllers:
            table_html += f'<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:center;vertical-align:top" colspan="2">{agent.upper()}</th>'
        table_html += '</tr><tr>'
        for _ in controllers:
            table_html += '<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top">CS</th><th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top">WCS</th>'
        table_html += '</tr></thead><tbody>'
        
        total_scores = {agent: 0 for agent in controllers}
        for metric, metric_name in [('avg_wait_time', 'Avg Wait Time (s)'), ('avg_queue_length', 'Avg Queue Length'), ('total_throughput', 'Total Throughput')]:
            weight = weights[metric]
            table_html += f'<tr><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{metric_name}</td>'
            table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{weight:.2f}</td>'
            for agent in controllers:
                cs = ranks.loc[agent, f'{metric}_rank']
                wcs = cs * weight
                total_scores[agent] += wcs
                table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{cs:.2f}</td><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{wcs:.2f}</td>'
            table_html += '</tr>'

        table_html += '<tr><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top" colspan="2"><b>Total Score</b></td>'
        for agent in controllers:
            table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top" colspan="2"><b>{total_scores[agent]:.2f}</b></td>'
        table_html += '</tr></tbody></table>'
        content += table_html

    content += '<h2>Sensitivity Analysis Summary</h2>'
    summary_df = sensitivity_results.T
    content += summary_df.to_html(border=1, classes="tg")

    # --- Generate HTML Content ---
    content = '<h1>Multiple Constraints and Tradeoff Analysis</h1>'
    
    content += '<h3>Raw Performance Data</h3>'
    content += df[[col for col in df.columns if '%' not in col]].to_html(border=1, classes="tg")

    content += '<h3>Subordinate Rank Calculation (Criterion Scores)</h3>'
    content += ranks.to_html(border=1, classes="tg")

    content += '<h2>Trade-off Analysis Tables</h2>'
    table_df_wait = pd.DataFrame({
        'Controller': df.index,
        'Average Wait Time (s)': df['avg_wait_time'],
        '% Difference': (df['avg_wait_time_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['avg_wait_time_rank']
    }).reset_index(drop=True)
    content += '<h3>Table X - Average Wait Time Comparison (Lower is Better)</h3>'
    content += table_df_wait.to_html(index=False, border=1, classes="tg")

    table_df_queue = pd.DataFrame({
        'Controller': df.index,
        'Average Queue Length': df['avg_queue_length'],
        '% Difference': (df['avg_queue_length_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['avg_queue_length_rank']
    }).reset_index(drop=True)
    content += '<h3>Table Y - Average Queue Length Comparison (Lower is Better)</h3>'
    content += table_df_queue.to_html(index=False, border=1, classes="tg")

    table_df_throughput = pd.DataFrame({
        'Controller': df.index,
        'Total Throughput': df['total_throughput'],
        '% Difference': (df['total_throughput_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['total_throughput_rank']
    }).reset_index(drop=True)
    content += '<h3>Table Z - Total Throughput Comparison (Higher is Better)</h3>'
    content += table_df_throughput.to_html(index=False, border=1, classes="tg")

    table_df_reward = pd.DataFrame({
        'Controller': df.index,
        'Total Reward': df['total_reward'],
        '% Difference': (df['total_reward_%diff'] * 100).round(2).astype(str) + '%',
        'Rank': ranks['total_reward_rank']
    }).reset_index(drop=True)
    content += '<h3>Table W - Total Reward Comparison (Higher is Better)</h3>'
    content += table_df_reward.to_html(index=False, border=1, classes="tg")

    content += '<h2>Sensitivity Analysis Tables</h2>'
    metric_names = {
        'avg_wait_time': 'Avg Wait Time (s)',
        'avg_queue_length': 'Avg Queue Length',
        'total_throughput': 'Total Throughput',
        'total_reward': 'Total Reward'
    }

    for trial_name, weights in trials.items():
        controllers = df.index.tolist()
        num_controllers = len(controllers)
        table_html = f'<h3>{trial_name}</h3>'
        table_html += '<table style="border-collapse:collapse;border-spacing:0" class="tg"><thead>'
        table_html += '<tr><th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top" rowspan="3">Criteria</th>'
        table_html += '<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top" rowspan="3">Criterion Weight (CW)</th>'
        table_html += f'<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:center;vertical-align:top" colspan="{num_controllers * 2}">Algorithm Weighted Score</th></tr>'
        table_html += '<tr>'
        for agent in controllers:
            table_html += f'<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:center;vertical-align:top" colspan="2">{agent.upper()}</th>'
        table_html += '</tr><tr>'
        for _ in controllers:
            table_html += '<th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top">CS</th><th style="border-color:black;border-style:solid;border-width:1px;font-weight:normal;padding:10px 5px;text-align:left;vertical-align:top">WCS</th>'
        table_html += '</tr></thead><tbody>'
        
        total_scores = {agent: 0 for agent in controllers}
        for metric, metric_name in metric_names.items():
            weight = weights[metric]
            table_html += f'<tr><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{metric_name}</td>'
            table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{weight:.2f}</td>'
            for agent in controllers:
                cs = ranks.loc[agent, f'{metric}_rank']
                wcs = cs * weight
                total_scores[agent] += wcs
                table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{cs:.2f}</td><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top">{wcs:.2f}</td>'
            table_html += '</tr>'

        table_html += '<tr><td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top" colspan="2"><b>Total Score</b></td>'
        for agent in controllers:
            table_html += f'<td style="border-color:black;border-style:solid;border-width:1px;padding:10px 5px;text-align:left;vertical-align:top" colspan="2"><b>{total_scores[agent]:.2f}</b></td>'
        table_html += '</tr></tbody></table>'
        content += table_html

    content += '<h2>Sensitivity Analysis Summary</h2>'
    summary_df = sensitivity_results.T
    content += summary_df.to_html(border=1, classes="tg")

    # --- Write to file ---
    with open(output_file, 'w') as f:
        f.write(HTML_TEMPLATE.format(content=content))
    
    print(f"Analysis complete. Report saved to {output_file}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate analysis report from results.csv.')
    parser.add_argument('--output', type=str, default='analysis_report.html', help='Path to the output HTML file.')
    args = parser.parse_args()
    main(args.output)