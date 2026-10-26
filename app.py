t5.metric("Profit factor", "∞" if pf == float("inf") else f"{pf:.2f}")
            t6.metric("Win rate", f"{bt['win_rate']:.1f}%")
            t7, t8, t9 = st.columns(3)
            t7.metric("Closed trades", str(bt["num_trades"]))
            t8.metric("Sharpe proxy", f"{bt['sharpe']:.3f}")
            t9.metric("Annual volatility", f"{bt['annual_volatility']:.1f}%")
            st.write(f"**Modal akhir:** Rp {bt['final_capital']:,.0f}")
            if bt["mdd"] < -20:
                st.warning("Drawdown historis lebih dari 20%; strategi dapat mengalami penurunan modal besar.")
            if pf != float("inf") and bt["num_trades"] > 0 and pf < 1:
                st.error("Profit factor < 1: total loss trade melebihi total profit trade untuk periode ini.")
            elif pf > 1.5:
                st.success("Profit factor historis > 1.5, tetapi tetap periksa jumlah trade, regime, dan out-of-sample.")

            eq_dates = data.index[-len(bt["equity_curve"]):]
            equity_df = pd.DataFrame({"Date": eq_dates, "Equity": bt["equity_curve"]})
            fig_eq = go.Figure(go.Scatter(x=equity_df["Date"], y=equity_df["Equity"], mode="lines", name="Equity"))
            fig_eq.update_layout(title="Equity curve selepas biaya", xaxis_title="Tanggal", yaxis_title="Nilai (Rp)", height=400)
            st.plotly_chart(fig_eq, use_container_width=True)
            with st.expander("Detail transaksi"):
                if bt["transactions"]:
                    st.dataframe(pd.DataFrame(bt["transactions"], columns=["Type", "Date", "Fill price", "Shares"]),
                                 use_container_width=True, hide_index=True)
                else:
                    st.info("Tidak ada transaksi.")
            with st.expander("P&L per round trip"):
                if bt["closed_trades"]:
                    closed_df = pd.DataFrame(bt["closed_trades"])
                    st.dataframe(closed_df, use_container_width=True, hide_index=True)
                    st.download_button("Download trade log CSV", closed_df.to_csv(index=False).encode("utf-8"),
                                       file_name="backtest_trades.csv", mime="text/csv")
                else:
                    st.info("Belum ada transaksi tertutup.")
    st.caption("Catatan: backtest belum memodelkan antrean bid/offer, ARB/ARA, suspensi, pajak, dampak pasar, dan seluruh corporate action. Hasil in-sample bukan bukti edge yang bertahan.")

# -----------------------------------------------------------------------------
# TAB 6: Fundamentals and glossary
# -----------------------------------------------------------------------------
with tab6:
    if ticker.startswith("^") or "=" in ticker:
        st.info("Instrumen indeks/FX tidak memiliki fundamental emiten.")
    else:
        st.subheader("Fundamental dari Yahoo Finance")
        fund = get_fundamental_details(ticker)
        quality = fundamental_quality_score(ticker)
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("PER (TTM)", "N/A" if fund.get("pe") is None else f"{fund['pe']:.2f}")
        f2.metric("PBV", "N/A" if fund.get("pb") is None else f"{fund['pb']:.2f}")
        div_yield = fund.get("div_yield")
        if div_yield is not None:
            div_yield_str = f"{div_yield * 100:.2f}%" if div_yield <= 1 else f"{div_yield:.2f}%"
        else:
            div_yield_str = "N/A"
        f3.metric("Dividend yield", div_yield_str)
        f4.metric("Market cap (source currency)", "N/A" if fund.get("market_cap") is None else f"{fund['market_cap'] / 1e12:.2f} T (source currency)")
        f5, f6, f7, f8 = st.columns(4)
        f5.metric("ROE", "N/A" if fund.get("roe") is None else f"{fund['roe'] * 100:.2f}%")
        f6.metric("ROA", "N/A" if fund.get("roa") is None else f"{fund['roa'] * 100:.2f}%")
        f7.metric("Profit margin", "N/A" if fund.get("profit_margin") is None else f"{fund['profit_margin'] * 100:.2f}%")
        f8.metric("Revenue growth YoY", "N/A" if fund.get("revenue_growth") is None else f"{fund['revenue_growth'] * 100:.2f}%")
        f9, f10, f11 = st.columns(3)
        f9.metric("Earnings growth YoY", "N/A" if fund.get("earnings_growth") is None else f"{fund['earnings_growth'] * 100:.2f}%")
        f10.metric("Debt / equity (Yahoo field)", "N/A" if fund.get("debt_to_equity") is None else f"{fund['debt_to_equity']:.2f}")
        f11.metric("Quality proxy score", "N/A" if quality is None else f"{quality * 100:.1f}/100")
        st.caption(f"Sektor terdeteksi Yahoo: {fund.get('sector') or 'N/A'}. Data fundamental bisa kosong, terlambat, atau berbeda metodologi; bukan pengganti laporan keuangan emiten.")

    with st.expander("Glossary dan interpretasi"):
        st.markdown("""
- **RSI:** ukuran momentum, bukan sinyal beli tunggal.
- **SMA20/SMA50:** rata-rata harga; dipakai sebagai filter tren.
- **ATR(14):** ukuran volatilitas absolut, bukan prediksi arah.
- **Confirmed breakout:** close melampaui resistance 20 sesi sebelumnya sebesar nilai terbesar antara 0,5% resistance dan 0,5×ATR.
- **Flow proxy:** gabungan CMF, kemiringan Accumulation/Distribution, volume relatif dan posisi harga; bukan identifikasi bandar atau broker.
- **ML probability:** estimasi model Random Forest untuk klasifikasi return positif 5 sesi; belum tentu terkalibrasi, dan bisa gagal saat regime berubah.
- **Walk-forward:** evaluasi dengan pelatihan pada masa lalu dan pengujian pada periode setelahnya, disertai jeda untuk mengurangi tumpang-tindih label.
- **Fundamental quality score:** proxy profitabilitas/pertumbuhan/leverage; tidak sama dengan fair value dan tidak membandingkan valuasi secara penuh antar sektor.
- **MDD:** penurunan terbesar dari puncak ekuitas.
- **Profit factor:** total profit trade dibagi total loss trade.
- **Position sizing:** jumlah saham dihitung dari risiko modal dan jarak harga ke stop, kemudian dibatasi modal dan lot size.
        """)

# -----------------------------------------------------------------------------
# TAB 7: Flow proxy
# -----------------------------------------------------------------------------
with tab7:
    st.header("Flow proxy — bukan broker summary")
    score, status = calculate_smart_money(data)
    if score is None:
        st.warning("Data minimal 20 baris belum tersedia; proxy tidak dihitung.")
    else:
        a, b = st.columns(2)
        a.metric("Flow proxy score", f"{score}/4")
        b.metric("Status", status)
        cmf_positive = safe_last(data["CMF"]) > 0
        ad_up_component = len(data) >= 6 and safe_last(data["AD"]) > safe_float(data["AD"].iloc[-6], 0.0)
        vol_now = safe_last(data["Volume"])
        vol_ma = safe_last(data["Volume_MA"])
        vol_ok = has_volume(data["Volume"]) and vol_ma > 0 and vol_now > vol_ma * 1.5
        price_ok = last_close > safe_last(data["SMA20"])
        st.write(f"CMF20 > 0: **{cmf_positive}**")
        st.write(f"AD line naik dibanding 5 sesi lalu: **{ad_up_component}**")
        st.write(f"Volume > 1,5× rata-rata sesi sebelumnya: **{vol_ok}**")
        st.write(f"Harga > SMA20: **{price_ok}**")
        st.warning("Indikator berbasis harga/volume tidak bisa membuktikan siapa pembelinya. Untuk foreign flow aktual, gunakan data resmi BEI/penyedia data dan input manual di tab AI Signal.")

# -----------------------------------------------------------------------------
# TAB 8: Macro
# -----------------------------------------------------------------------------
with tab8:
    st.header("Macro market filter")
    macro_status, macro_score, macro_components = get_macro_signal()
    colm1, colm2 = st.columns(2)
    colm1.metric("Macro condition", macro_status)
    known_macro_feeds = sum(v is not None for v in macro_components.values())
    colm2.metric("Known positive votes", f"{macro_score}/{known_macro_feeds}")
    macro_data = get_macro_data()
    tickers_macro = [("^JKSE", "IHSG"), ("USDIDR=X", "USD/IDR"), ("^IXIC", "Nasdaq Composite")]
    mcols = st.columns(3)
    for idx, (symbol, label) in enumerate(tickers_macro):
        series = macro_data.get(symbol, pd.Series(dtype=float))
        if len(series) >= 2:
            period_return = (safe_last(series) / safe_float(series.iloc[0], safe_last(series)) - 1) * 100
            mcols[idx].metric(label, f"{safe_last(series):,.2f}", f"{period_return:+.2f}% over loaded period")
        else:
            mcols[idx].metric(label, "N/A")
    st.write("**Komponen filter:**")
    for symbol, label in [("^JKSE", "IHSG di atas rata-rata"), ("USDIDR=X", "USD/IDR di bawah rata-rata (rupiah menguat)"), ("^IXIC", "Nasdaq di atas rata-rata")]:
        value = macro_components.get(symbol)
        st.write(f"{label}: **{'Positif' if value is True else 'Negatif' if value is False else 'Data tidak tersedia'}**")
    st.caption("Filter makro bersifat sederhana: membandingkan harga terakhir dengan rata-rata data historis yang tersedia. Foreign flow aktual, BI Rate, SUN yield dan komoditas belum diambil otomatis.")

# -----------------------------------------------------------------------------
# TAB 9: Sector rotation
# -----------------------------------------------------------------------------
with tab9:
    st.header("Sector rotation proxy")
    best_sector, sector_data = get_sector_rotation()
    st.metric("Leading sector (return 5 sesi rata-rata)", best_sector)
    if sector_data:
        sector_df = pd.DataFrame(list(sector_data.items()), columns=["Sektor", "Return 5 Sesi"])
        sector_df = sector_df.sort_values("Return 5 Sesi", ascending=False)
        st.dataframe(sector_df.assign(**{"Return 5 Sesi (%)": sector_df["Return 5 Sesi"] * 100}).drop(columns=["Return 5 Sesi"]),
                     use_container_width=True, hide_index=True)
        st.bar_chart(sector_df.set_index("Sektor")["Return 5 Sesi"])
    else:
        st.info("Data sektor tidak cukup saat ini.")
    st.caption("Sektor diproksikan oleh sampel saham, bukan seluruh konstituen sektor. Bobot antar saham sama.")

st.divider()
st.caption("⚠️ Disclaimer: aplikasi ini untuk edukasi dan analisis otomatis, bukan rekomendasi beli/jual. Data Yahoo Finance dapat terlambat/tidak lengkap. Keputusan investasi dan risiko transaksi tetap pada pengguna.")
gc.collect()
