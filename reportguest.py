import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime

st.title("📊 Guest Posting Report Generator")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Standardize column names
        column_map = {
            "Taregt Keyword - 1": "Target Keyword - 1",
            "Taregt  Keyword-1 URL": "Target Keyword-1 URL",
            "Taregt Keyword - 2": "Target Keyword - 2",
            "Taregt Keyword - 2 (URL)": "Target Keyword-2 URL",
            "Taregt Keyword - 3": "Target Keyword - 3",
            "Target Keyword-3 URL": "Target Keyword-3 URL",
            "Taregt Keyword - 4": "Target Keyword - 4",
            "Target Keyword-4 URL": "Target Keyword-4 URL",
            "Taregt Keyword - 5": "Target Keyword - 5",
            "Target Keyword-5 URL": "Target Keyword-5 URL",
        }

        df.rename(columns=column_map, inplace=True)

        # Convert "Publish Date" to datetime format
        df["Publish Date"] = pd.to_datetime(df["Publish Date"], errors="coerce")

        # Extract Month & Year for filtering
        df["Month"] = df["Publish Date"].dt.strftime("%Y-%m")

        # Extract keyword & URL columns dynamically
        keyword_cols = [col for col in df.columns if "Target Keyword -" in col and "URL" not in col]
        url_cols = [col for col in df.columns if "Target Keyword-" in col and "URL" in col]

        keyword_data = pd.melt(df, id_vars=["Live Link", "Title", "Publish Date", "Month"],
                               value_vars=keyword_cols, var_name="Keyword Column", value_name="Keyword")

        url_data = pd.melt(df, id_vars=["Live Link", "Title", "Publish Date", "Month"],
                           value_vars=url_cols, var_name="URL Column", value_name="URL")

        merged_df = pd.concat([keyword_data, url_data["URL"]], axis=1)
        merged_df = merged_df.dropna(subset=["Keyword", "URL"])

        st.subheader("📌 Data Overview")
        st.dataframe(merged_df)

        # 🔍 Filters
        st.sidebar.header("📍 Filters")
        selected_keyword = st.sidebar.selectbox("🔑 Filter by Keyword",
                                                ["All"] + sorted(merged_df["Keyword"].dropna().unique().tolist()))
        selected_url = st.sidebar.selectbox("🔗 Filter by URL",
                                            ["All"] + sorted(merged_df["URL"].dropna().unique().tolist()))

        # 📅 Date Filters: Select specific date OR date range
        st.sidebar.subheader("📅 Filter by Date")
        filter_option = st.sidebar.radio("Select Date Filter:", ["Specific Date", "Date Range"])

        if filter_option == "Specific Date":
            selected_date = st.sidebar.date_input("📅 Choose Date", value=None)
        else:
            start_date = st.sidebar.date_input("📅 Start Date", value=None)
            end_date = st.sidebar.date_input("📅 End Date", value=None)

        # Apply filters
        filtered_df = merged_df.copy()
        if selected_keyword != "All":
            filtered_df = filtered_df[filtered_df["Keyword"] == selected_keyword]
        if selected_url != "All":
            filtered_df = filtered_df[filtered_df["URL"] == selected_url]

        if filter_option == "Specific Date" and selected_date:
            filtered_df = filtered_df[filtered_df["Publish Date"] == pd.to_datetime(selected_date)]
        elif filter_option == "Date Range" and start_date and end_date:
            filtered_df = filtered_df[
                (filtered_df["Publish Date"] >= pd.to_datetime(start_date)) &
                (filtered_df["Publish Date"] <= pd.to_datetime(end_date))
                ]

        st.subheader("🔍 Filtered Results")
        st.dataframe(filtered_df)

        # 🔥 Monthly Summary
        st.subheader("📅 Monthly Summary")
        unique_months = merged_df["Month"].unique()
        selected_month = st.selectbox("📆 Select Month", sorted(unique_months, reverse=True))

        month_df = merged_df[merged_df["Month"] == selected_month]

        total_posts = month_df[month_df["Live Link"].notna()].shape[0]
        unique_keywords = month_df["Keyword"].nunique()
        unique_urls = month_df["URL"].nunique()

        st.write(f"✅ **Total Guest Posts Published:** {total_posts}")
        st.write(f"🔑 **Total Keywords Used:** {unique_keywords}")
        st.write(f"🔗 **Total URLs Used:** {unique_urls}")

        # Find URLs that did not get guest posts this month
        all_possible_urls = set(df[url_cols].stack().dropna().unique())
        used_urls = set(month_df["URL"].unique())
        unused_urls = all_possible_urls - used_urls

        if unused_urls:
            st.write("⚠ **URLs Without Guest Posts This Month:**")
            st.write(", ".join(unused_urls))
        else:
            st.write("🎉 All URLs received guest posts!")

        # 📊 Guest Posts by Date
        st.subheader("📈 Guest Posts Over Time")
        posts_by_date = month_df.groupby("Publish Date").size().reset_index(name="Post Count")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(posts_by_date["Publish Date"].dt.strftime("%Y-%m-%d"), posts_by_date["Post Count"], color="skyblue")
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Post Count")
        plt.title("Guest Posts by Date")
        st.pyplot(fig)

        # 🔍 **Compare Monthly Trends**
        st.subheader("📊 Compare Two Months")

        month_compare_1 = st.selectbox("📅 Select First Month", sorted(unique_months, reverse=True))
        month_compare_2 = st.selectbox("📅 Select Second Month", sorted(unique_months, reverse=True))

        if month_compare_1 and month_compare_2 and month_compare_1 != month_compare_2:
            df1 = merged_df[merged_df["Month"] == month_compare_1]
            df2 = merged_df[merged_df["Month"] == month_compare_2]

            summary = {
                "Total Posts": [df1[df1["Live Link"].notna()].shape[0], df2[df2["Live Link"].notna()].shape[0]],
                "Unique Keywords": [df1["Keyword"].nunique(), df2["Keyword"].nunique()],
                "Unique URLs": [df1["URL"].nunique(), df2["URL"].nunique()],
            }

            summary_df = pd.DataFrame(summary, index=[month_compare_1, month_compare_2])
            st.write(summary_df)

    except Exception as e:
        st.error(f"Error processing file: {e}")