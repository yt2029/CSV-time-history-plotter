import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------
# ファイル読み込み関数
# -----------------------
def load_file(uploaded_file, label_row, data_start_row):
    try:
        # 一旦全体を読み込む
        raw_df = pd.read_csv(uploaded_file, header=None)
        # 指定した行からカラム名、データ開始
        col_names = raw_df.iloc[label_row].tolist()
        df = raw_df.iloc[data_start_row:].copy()
        df.columns = col_names
        df['__source__'] = uploaded_file.name
        return df
    except Exception as e:
        st.error(f"{uploaded_file.name} の読み込みエラー: {e}")
        return None

# -----------------------
# プロット関数
# -----------------------
def plot_data(dfs, selected_columns, y2_columns):
    fig = go.Figure()
    all_data = pd.concat(dfs, ignore_index=True)

    time_min = pd.to_numeric(all_data['Time'], errors='coerce').min()
    time_max = pd.to_numeric(all_data['Time'], errors='coerce').max()

    y_values = pd.DataFrame()
    for df in dfs:
        for col in selected_columns + y2_columns:
            if col in df.columns:
                y_values = pd.concat([y_values, pd.to_numeric(df[col], errors="coerce")], axis=1)

    y_min = y_values.min().min()
    y_max = y_values.max().max()

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

    fig.update_layout(
        title='統合プロット',
        xaxis_title='Time',
        yaxis=dict(title='Data Value', range=[y_min, y_max]),
        yaxis2=dict(title='Second Data Value', overlaying='y', side='right'),
        hovermode='closest',
        autosize=True
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------
# Streamlit UI
# -----------------------
st.title('CSVデータ可視化ツール（ラベル/データ開始行 指定付き）')

uploaded_files = st.file_uploader("CSVファイルをアップロード（複数選択可）", type=["csv"], accept_multiple_files=True)

# 💡 ラベル行・データ開始行の指定UI（0-based）
label_row = st.number_input("データラベルの行（0ベース）", min_value=0, value=1, help="通常は2行目 = 1")
data_start_row = st.number_input("データ開始の行（0ベース）", min_value=0, value=2, help="通常は3行目 = 2")

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        df = load_file(uploaded_file, label_row, data_start_row)
        if df is not None and 'Time' in df.columns:
            dfs.append(df)
        else:
            st.warning(f"{uploaded_file.name} に 'Time' 列が見つかりません。スキップします。")

    if dfs:
        all_columns = set()
        for df in dfs:
            all_columns.update([col for col in df.columns if col not in ['Time', '__source__']])
        column_titles = sorted(all_columns)

        selected_columns = st.multiselect("選択するデータ列（最大6つ）", column_titles, max_selections=6)
        y2_columns = st.multiselect("第二軸に表示するデータ列", column_titles)

        if st.button("統合プロットを表示"):
            if selected_columns:
                plot_data(dfs, selected_columns, y2_columns)
            else:
                st.warning("プロットするデータ列を選択してください。")
