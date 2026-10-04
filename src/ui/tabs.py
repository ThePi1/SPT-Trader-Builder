"""Tab bars whose pages are drawn in Qt Designer: each tab is an empty page in the .ui file with its title,
position, tooltip and icon, and the code swaps the real widget in for it."""


def fill_tabs(tabs, owner, pages):
	"""Replace the placeholder pages of a tab widget with the real widgets.

	tabs: the QTabWidget. owner: the object the .ui file's widgets are attributes of (the placeholders are
	owner.page_xxx). pages: {placeholder name: the widget that replaces it}. A tab keeps what its page had in
	Designer. The names in the .ui file and in pages must be the same, or RuntimeError says which they are.
	"""
	in_file = {tabs.widget(i).objectName() for i in range(tabs.count())}
	if in_file != set(pages):
		raise RuntimeError(f"the .ui file has the tab pages {sorted(in_file)}, but the code fills {sorted(pages)}")
	for name, widget in pages.items():
		placeholder = getattr(owner, name)
		index = tabs.indexOf(placeholder)
		title, tip, icon = tabs.tabText(index), tabs.tabToolTip(index), tabs.tabIcon(index)
		tabs.removeTab(index)
		placeholder.hide()
		placeholder.deleteLater()
		delattr(owner, name)
		tabs.insertTab(index, widget, icon, title)
		tabs.setTabToolTip(index, tip)
	tabs.setCurrentIndex(0)
