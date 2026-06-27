import streamlit as st
from config import DEFAULT_CLUSTERS, COLOR_PALETTE, IBC_COLORS_DEFAULT


def _init_state():
    if "clusters" not in st.session_state:
        st.session_state["clusters"] = {k: list(v) for k, v in DEFAULT_CLUSTERS.items()}
    if "ibc_colors" not in st.session_state:
        st.session_state["ibc_colors"] = dict(IBC_COLORS_DEFAULT)


def get_clusters() -> dict:
    _init_state()
    return st.session_state["clusters"]


def get_all_ibcs() -> list:
    return sorted({ibc for ibcs in get_clusters().values() for ibc in ibcs})


def get_ibc_colors() -> dict:
    _init_state()
    return st.session_state["ibc_colors"]


def get_cluster_options() -> list:
    return ["All Clusters"] + list(get_clusters().keys())


def get_ibc_options() -> list:
    return ["All IBCs"] + get_all_ibcs()


def get_color_list() -> list:
    colors = get_ibc_colors()
    return [colors.get(ibc, COLOR_PALETTE[i % len(COLOR_PALETTE)])
            for i, ibc in enumerate(get_all_ibcs())]


def get_target_rr() -> dict:
    if "target_rr" not in st.session_state:
        st.session_state["target_rr"] = {ibc: 80.0 for ibc in get_all_ibcs()}
    for ibc in get_all_ibcs():
        if ibc not in st.session_state["target_rr"]:
            st.session_state["target_rr"][ibc] = 80.0
    return st.session_state["target_rr"]

def get_potential_target() -> dict:
    """Get potential target per IBC — default 0 for all."""
    if "potential_target" not in st.session_state:
        st.session_state["potential_target"] = {ibc: 0.0 for ibc in get_all_ibcs()}
    for ibc in get_all_ibcs():
        if ibc not in st.session_state["potential_target"]:
            st.session_state["potential_target"][ibc] = 0.0
    return st.session_state["potential_target"]


def render_settings_page():
    st.markdown('<div class="dashboard-title">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Manage IBCs, Clusters and Targets</div>', unsafe_allow_html=True)
    st.markdown("---")

    _init_state()
    clusters   = st.session_state["clusters"]
    ibc_colors = st.session_state["ibc_colors"]

    # ── CLUSTER MANAGEMENT 
    st.markdown('<div class="section-header">🏢 Cluster Management</div>', unsafe_allow_html=True)

    with st.expander("➕ Add New Cluster", expanded=False):
        new_cluster_name = st.text_input("Cluster Name", placeholder="e.g. North Cluster", key="new_cluster_name")
        if st.button("Add Cluster", key="btn_add_cluster"):
            name = new_cluster_name.strip()
            if name:
                if name not in clusters:
                    clusters[name] = []
                    st.session_state["clusters"] = clusters
                    st.success(f"✅ '{name}' added!")
                    st.rerun()
                else:
                    st.warning("Already exists.")
            else:
                st.error("Name cannot be empty.")

    for cluster_name, ibc_list in list(clusters.items()):
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"**🏢 {cluster_name}** — {', '.join(ibc_list) if ibc_list else 'No IBCs'}")
        with c2:
            if st.button("🗑️ Delete", key=f"del_cluster_{cluster_name}"):
                del clusters[cluster_name]
                st.session_state["clusters"] = clusters
                st.rerun()

    st.markdown("---")

    # ── IBC MANAGEMENT 
    st.markdown('<div class="section-header">📍 IBC Management</div>', unsafe_allow_html=True)

    with st.expander("➕ Add New IBC", expanded=False):
        a1, a2, a3 = st.columns(3)
        with a1:
            new_ibc_name = st.text_input("IBC Name", placeholder="e.g. Gulshan", key="new_ibc_name")
        with a2:
            cluster_keys = list(clusters.keys())
            if cluster_keys:
                assign_cluster = st.selectbox("Cluster", cluster_keys, key="new_ibc_cluster")
            else:
                st.warning("Add a cluster first.")
                assign_cluster = None
        with a3:
            new_ibc_color = st.selectbox("Color", COLOR_PALETTE, key="new_ibc_color")
            st.markdown(
                f'<div style="width:100%;height:10px;background:{new_ibc_color};border-radius:4px;margin-top:4px"></div>',
                unsafe_allow_html=True,
            )

        if st.button("Add IBC", key="btn_add_ibc"):
            ibc = new_ibc_name.strip()
            if ibc and assign_cluster:
                if ibc in get_all_ibcs():
                    st.warning(f"'{ibc}' already exists.")
                else:
                    clusters[assign_cluster].append(ibc)
                    ibc_colors[ibc] = new_ibc_color
                    st.session_state["clusters"]   = clusters
                    st.session_state["ibc_colors"] = ibc_colors
                    st.success(f"✅ '{ibc}' added to '{assign_cluster}'!")
                    st.rerun()
            else:
                st.error("IBC name and cluster required.")

    # List all IBCs
    all_ibcs = get_all_ibcs()
    if all_ibcs:
        st.markdown("**All IBCs:**")
        for ibc in all_ibcs:
            current_cluster = next((c for c, il in clusters.items() if ibc in il), None)
            color = ibc_colors.get(ibc, "#58a6ff")
            i1, i2, i3, i4 = st.columns([2, 2, 1, 1])
            with i1:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:{color}"></div>'
                    f'<b>{ibc}</b></div>',
                    unsafe_allow_html=True,
                )
            with i2:
                cluster_keys = list(clusters.keys())
                idx = cluster_keys.index(current_cluster) if current_cluster in cluster_keys else 0
                new_cluster = st.selectbox(
                    "Cluster", cluster_keys, index=idx,
                    key=f"ibc_cluster_{ibc}", label_visibility="collapsed",
                )
                if new_cluster != current_cluster:
                    for c in clusters:
                        if ibc in clusters[c]:
                            clusters[c].remove(ibc)
                    clusters[new_cluster].append(ibc)
                    st.session_state["clusters"] = clusters
                    st.rerun()
            with i3:
                idx_c = COLOR_PALETTE.index(color) if color in COLOR_PALETTE else 0
                new_color = st.selectbox(
                    "Color", COLOR_PALETTE, index=idx_c,
                    key=f"ibc_color_{ibc}", label_visibility="collapsed",
                )
                if new_color != color:
                    ibc_colors[ibc] = new_color
                    st.session_state["ibc_colors"] = ibc_colors
                    st.rerun()
            with i4:
                if st.button("🗑️", key=f"del_ibc_{ibc}"):
                    for c in clusters:
                        if ibc in clusters[c]:
                            clusters[c].remove(ibc)
                    ibc_colors.pop(ibc, None)
                    st.session_state["clusters"]   = clusters
                    st.session_state["ibc_colors"] = ibc_colors
                    st.rerun()

    st.markdown("---")

    # ── TARGET RR 
    st.markdown('<div class="section-header">🎯 Target RR per IBC</div>', unsafe_allow_html=True)
    st.caption("Set a separate target recovery rate for each IBC.")

    target_rr = get_target_rr()
    all_ibcs  = get_all_ibcs()
    cols      = st.columns(3)

    for i, ibc in enumerate(all_ibcs):
        with cols[i % 3]:
            val = st.number_input(
                ibc,
                min_value=0.0,
                max_value=200.0,
                value=float(target_rr.get(ibc, 80.0)),
                step=0.5,
                format="%.1f",
                key=f"target_rr_{ibc}",
            )
            target_rr[ibc] = val

    if st.button("💾 Save Target RR", key="btn_save_target_rr", type="primary"):
        st.session_state["target_rr"] = target_rr
        st.success("✅ Target RR saved!")

    st.markdown("---")
    st.markdown("---")

    # ── POTENTIAL TARGET 
    st.markdown('<div class="section-header">🎯 Potential Target per IBC (PKR)</div>', unsafe_allow_html=True)
    st.caption("Manually set the potential target for each IBC in PKR.")

    potential_target = get_potential_target()
    cols2 = st.columns(3)

    for i, ibc in enumerate(all_ibcs):
        with cols2[i % 3]:
            val = st.number_input(
                ibc,
                min_value=0.0,
                value=float(potential_target.get(ibc, 0.0)),
                step=100000.0,
                format="%.0f",
                key=f"pot_target_{ibc}",
                help="PKR mein enter karo",
            )
            potential_target[ibc] = val

    if st.button("💾 Save Potential Target", key="btn_save_pot_target", type="primary"):
        st.session_state["potential_target"] = potential_target
        st.success("✅ Potential Target saved!")

    # ── RESET 
    st.markdown('<div class="section-header">⚠️ Reset to Defaults</div>', unsafe_allow_html=True)
    if st.button("🔄 Reset All to Default", key="btn_reset_defaults", type="secondary"):
        for key in ["clusters", "ibc_colors", "target_rr"]:
            st.session_state.pop(key, None)
        st.success("✅ Reset done!")
        st.rerun()