import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Wide mode に設定
st.set_page_config(layout="wide")

# ファイル読み込み関数（スキップ行数を動的に設定）
def load_file(uploaded_file, skiprows):
    try:
        df = pd.read_csv(uploaded_file, skiprows=skiprows)
        df['__source__'] = uploaded_file.name  # ファイル名を記録
        return df
    except Exception as e:
        st.error(f"{uploaded_file.name} の読み込みエラー: {e}")
        return None

# プロット関数（複数ファイルを統合）
def plot_data(dfs, selected_columns, y2_columns):
    fig = go.Figure()
    all_data = pd.concat(dfs, ignore_index=True)
    
    # X軸スケール（Timeの共通範囲）
    time_min = pd.to_numeric(all_data['Time'], errors='coerce').min()
    time_max = pd.to_numeric(all_data['Time'], errors='coerce').max()
    all_data_filtered = all_data[all_data['Time'].between(time_min, time_max)]

    # Y軸スケーリング範囲を決定（選択列すべてから）
    y_values = pd.DataFrame()
    for df in dfs:
        for col in selected_columns + y2_columns:
            if col in df.columns:
                y_values = pd.concat([y_values, pd.to_numeric(df[col], errors="coerce")], axis=1)

    y_min = y_values.min().min()
    y_max = y_values.max().max()

    # 各ファイルの各列をプロット
    for df in dfs:
        source = df['__source__'].iloc[0]
        time_data = pd.to_numeric(df['Time'], errors='coerce')

        for col in selected_columns:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=time_data,
                    y=pd.to_numeric(df[col], errors="coerce"),
                    mode='lines',
                    name=f"{source} - {col}"
                ))

        for col in y2_columns:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=time_data,
                    y=pd.to_numeric(df[col], errors="coerce"),
                    mode='lines',
                    name=f"{source} - {col} (y2)",
                    yaxis='y2'
                ))

    # レイアウト調整（凡例下・高さ700）
    fig.update_layout(
        height=700,
        xaxis_title='Time',
        yaxis=dict(title='Data Value', range=[y_min, y_max]),
        yaxis2=dict(title='Second Data Value', overlaying='y', side='right'),
        hovermode='closest',
        autosize=True,
        legend=dict(
            orientation="h",
            x=0.5,
            y=-0.2,
            xanchor="center",
            yanchor="top"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------
# Streamlit UI
# ----------------------------------
st.title('CSVデータプロットツール')

# ✅ スキップする行数をGUIから指定
skiprows = st.number_input("CSVの先頭でスキップする行数", min_value=0, max_value=10, value=1, step=1)

# ✅ ファイルアップロード
uploaded_files = st.file_uploader("CSVファイルをアップロード（複数選択可）", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = load_file(uploaded_file, skiprows=skiprows)
        if df is not None and 'Time' in df.columns:
            dfs.append(df)
        else:
            st.warning(f"{uploaded_file.name} に 'Time' 列がありません。スキップします。")

    if dfs:
        # ✅ 全ファイルの列名を統合して選択肢に
        all_columns = set()
        for df in dfs:
            all_columns.update([col for col in df.columns if col not in ['Time', '__source__']])
        column_titles = sorted(all_columns)

        # ✅ データ列の選択（複数OK）
        selected_columns = st.multiselect("選択するデータ列（最大6つ）", column_titles, max_selections=6)
        y2_columns = st.multiselect("第二軸に表示するデータ列", column_titles)

        # ✅ プロットボタン
        if st.button("統合プロットを表示"):
            if selected_columns:
                plot_data(dfs, selected_columns, y2_columns)
            else:
                st.warning("プロットするデータ列を選択してください。")
