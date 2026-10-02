import copy

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox

from modules.builders import conditions
from modules.gui.compiled.gui_tasks import Ui_TaskWindow
from modules.state import TableFields
from modules.table_fields import add_table_field, remove_selected_table_item
from modules.utils import is_true, new_id, val_field
from modules.windows.common import select_id, select_or_add


# Where the form of each kind of top-level task is: the tab widgets down to it, as (tab widget, page)
# attribute names of the UI, and the button that finishes it. (FindItem and HandoverItem share a form.)
TASK_TABS = {
	"CounterCreator": (("tabWidget_2", "tab"), ("tabWidget", "tab_6")),
	"Item": (("tabWidget_2", "tab"), ("tabWidget", "tab_handover_item")),
	"Skill": (("tabWidget_2", "tab"), ("tabWidget", "tb_Skill")),
	"LeaveItemAtLocation": (("tabWidget_2", "tab"), ("tabWidget", "tab_leave_item")),
	"PlaceBeacon": (("tabWidget_2", "tab"), ("tabWidget", "tab_7")),
	"TraderLoyalty": (("tabWidget_2", "tab"), ("tabWidget", "tab_trader_loyalty")),
	"Level": (("tabWidget_2", "tab_2"), ("tabWidget_3", "tab_3")),
	"TraderStanding": (("tabWidget_2", "tab_2"), ("tabWidget_3", "tab_5")),
	"Quest": (("tabWidget_2", "tab_17"), ("tabWidget_8", "tab_33")),
}
FINISH_BUTTONS = {
	"CounterCreator": "pb_finalize_cc",
	"Item": "pb_finalize_it",
	"Skill": "pb_finalize_sk",
	"LeaveItemAtLocation": "pb_finalize_li",
	"PlaceBeacon": "pb_finalize_pb",
	"TraderLoyalty": "pb_finalize_tl",
	"Level": "pb_finalize_lv",
	"Quest": "pb_finalize_qs",
	"TraderStanding": "pb_finalize_ts",
}


# The page of the Counter's sub-condition tabs that holds each kind of sub-condition's form, and the button that finishes it
SUB_TABS = {
	"VisitPlace": "tab_11",
	"Kills": "tab_12",
	"ExitStatus": "tab_20",
	"ExitName": "tab_21",
	"Location": "tab_22",
	"Equipment": "tab_9",
	"Shots": "tab_10",
	"HealthEffect": "tab_13",
	"HealthBuff": "tab_14",
	"LaunchFlare": "tab_23",
	"InZone": "tab_24",
}
SUB_BUTTONS = {
	"VisitPlace": "pb_finalize_ccvp",
	"Kills": "pb_finalize_cck",
	"ExitStatus": "pb_finalize_cces",
	"ExitName": "pb_finalize_ccen",
	"Location": "pb_finalize_ccl",
	"Equipment": "pb_finalize_cc_eq",
	"Shots": "pb_finalize_shtr",
	"HealthEffect": "pb_finalize_he",
	"HealthBuff": "pb_finalize_hb",
	"LaunchFlare": "pb_finalize_fl",
	"InZone": "pb_finalize_iz",
}


def can_edit_subcondition(sub):
	"""Whether the Task Builder can open this sub-condition of a Counter (not Arena ones, UseItem, ...)."""
	return sub.get("conditionType") in conditions.SUBCONDITION_EDITABLE_KEYS


def flat(groups):
	"""A list of mods, or of groups of mods (several mods in one inner list), as one flat list."""
	out = []
	for entry in groups or []:
		out.extend(entry if isinstance(entry, list) else [entry])
	return out


def can_edit(condition):
	"""Whether the Task Builder can open this condition (it can't, for kinds it can't make)."""
	return condition.get("conditionType") in conditions.EDITABLE_KEYS


def dialog_type(condition):
	"""The name the dialog uses for a condition's kind ("Item" covers FindItem and HandoverItem)."""
	kind = condition["conditionType"]
	return "Item" if kind in ("FindItem", "HandoverItem") else kind


def visibility_target(entry):
	"""The task a visibility condition points at (older exports wrote just the id)."""
	return entry["target"] if isinstance(entry, dict) else str(entry)


class Gui_TaskDlg(QMainWindow):
	# (timing, condition_type, condition_id, condition) - sent when the user finalizes a condition
	condition_ready = Signal(str, str, str, object)

	def __init__(self, state, parent=None, condition=None, timing=None):
		"""A new task, or (if condition is given) an existing one to edit.

		condition is the condition dict and timing the list it is in (Start, Finish or Fail). The
		dialog works on a copy: nothing changes until the task is saved. ValueError if the condition
		is of a kind the dialog can't make.
		"""
		super().__init__(parent)
		if condition is not None and not can_edit(condition):
			raise ValueError(f"The Task Builder can't edit tasks of type {condition.get('conditionType')!r}")
		self.ui = Ui_TaskWindow()
		self.ui.setupUi(self)
		self.state = state
		self.fields = TableFields()  # this dialog's own table rows
		self.original = copy.deepcopy(condition) if condition is not None else None  # None for a new task
		self.baseline = None  # what the form built straight after it was filled from the original
		self.visibility_objects = {}  # target -> its visibility condition (see visibility_object)
		self.fixed_timing = timing if condition is not None and timing else "Start"  # (for the start-only kinds)
		# name shown in the boxes -> what is written, for the boxes that show a name
		self.trader_ids = dict(state.traders)
		self.status_ids = dict(state.status)
		self.weapon_ids = dict(state.weapons)
		self.sub_edit = None  # the Counter's sub-condition being edited: {original, baseline, type, button text}
		self.id = self.original["id"] if self.original is not None else new_id()
		self.cc = []
		# self.weapons = [] # used for CC/Kills, add ids in as needed
		# self.status = [] # used for CC/exitstatus
		# self.location = [] # used for cc/location
		self.on_launch()  # Custom code in this one
		if self.original is not None:
			self.load_condition(self.original, timing)
		self.show()

	def on_launch(self):
		self.setup_box_selections()
		self.setup_text_edit()
		self.setup_buttons()

	def setup_box_selections(self):
		ctr = self.state.config
		self.ui.box_targets_cck.addItems(ctr.tb_elim_box_target)
		self.ui.box_targetrole_cck.addItems(ctr.tb_elim_box_targetrole)
		self.ui.box_bodypart_cck.addItems(ctr.tb_elim_box_bodypart)
		self.ui.box_dist_compare_cck.addItems(ctr.default_compare)
		self.ui.box_weapons_cck.addItems(ctr.tb_elim_box_weapons)
		self.ui.box_status_cces.addItems(ctr.tb_exitstatus)
		self.ui.box_location_ccl.addItems(ctr.qb_box_location)
		self.ui.box_hofind_it.addItems(ctr.tb_handover_box_cond_type)
		self.ui.box_only_fir_it.addItems(ctr.default_ft)
		self.ui.box_compare_sk.addItems(ctr.default_compare)
		self.ui.box_target_sk.addItems(ctr.default_skills)
		self.ui.box_fir_li.addItems(ctr.default_ft)
		self.ui.box_compare_tl.addItems(ctr.default_compare)
		self.ui.box_target_tl.addItems(self.state.traders.keys())
		self.ui.box_compare_lv.addItems(ctr.default_compare)
		self.ui.box_status_qs.addItems(ctr.tb_queststatus)
		self.ui.box_timing_qs.addItems(ctr.tb_any)
		self.ui.box_comparemethod_ts.addItems(ctr.default_compare)
		self.ui.box_cc_qtlab.addItems(ctr.qb_box_quest_type_label)
		self.ui.box_ff.addItems(ctr.tb_finishfail)
		self.ui.box_ff_it.addItems(ctr.tb_finishfail)
		self.ui.box_ff_sk.addItems(ctr.tb_finishfail)
		self.ui.box_ff_li.addItems(ctr.tb_finishfail)
		self.ui.box_ff_pb.addItems(ctr.tb_finishfail)
		self.ui.box_ff_tl.addItems(ctr.tb_finishfail)
		self.ui.box_trader_ts.addItems(self.state.traders.keys())
		self.ui.box_distcomp_sh.addItems(ctr.default_compare)
		self.ui.box_target_sh.addItems(ctr.tb_elim_box_target)
		self.ui.box_shbp.addItems(ctr.tb_elim_box_bodypart)
		self.ui.box_shtr.addItems(ctr.tb_elim_box_targetrole)
		self.ui.box_encomp_he.addItems(ctr.default_compare)
		self.ui.box_hydcomp_he.addItems(ctr.default_compare)
		self.ui.box_timecomp_he.addItems(ctr.default_compare)
		self.ui.box_hebp.addItems(ctr.tb_elim_box_bodypart)
		self.ui.box_heef.addItems(ctr.tb_effect)
		self.ui.box_hb.addItems(ctr.tb_buff)

	def setup_buttons(self):
		# CounterCreator types first:
		self.ui.pb_finalize_ccvp.released.connect(lambda: self.cc_add("VisitPlace"))
		self.ui.pb_finalize_cck.released.connect(lambda: self.cc_add("Kills"))
		self.ui.pb_finalize_cces.released.connect(lambda: self.cc_add("ExitStatus"))
		self.ui.pb_finalize_ccen.released.connect(lambda: self.cc_add("ExitName"))
		self.ui.pb_finalize_ccl.released.connect(lambda: self.cc_add("Location"))
		self.ui.pb_finalize_cc_eq.released.connect(lambda: self.cc_add("Equipment"))
		self.ui.pb_finalize_shtr.released.connect(lambda: self.cc_add("Shots"))
		self.ui.pb_finalize_he.released.connect(lambda: self.cc_add("HealthEffect"))
		self.ui.pb_finalize_hb.released.connect(lambda: self.cc_add("HealthBuff"))
		self.ui.pb_finalize_fl.released.connect(lambda: self.cc_add("LaunchFlare"))
		self.ui.pb_finalize_iz.released.connect(lambda: self.cc_add("InZone"))

		# Others:
		self.ui.pb_finalize_it.released.connect(
			lambda: self.finalize("Item")
		)  # will be switched based on subtype later
		self.ui.pb_finalize_sk.released.connect(lambda: self.finalize("Skill"))
		self.ui.pb_finalize_li.released.connect(
			lambda: self.finalize("LeaveItemAtLocation")
		)
		self.ui.pb_finalize_pb.released.connect(lambda: self.finalize("PlaceBeacon"))
		self.ui.pb_finalize_cc.released.connect(lambda: self.finalize("CounterCreator"))
		# TODO: Add WeaponAssembly menu and finalize link here
		self.ui.pb_finalize_tl.released.connect(lambda: self.finalize("TraderLoyalty"))
		self.ui.pb_finalize_lv.released.connect(lambda: self.finalize("Level"))
		self.ui.pb_finalize_qs.released.connect(lambda: self.finalize("Quest"))
		self.ui.pb_finalize_ts.released.connect(lambda: self.finalize("TraderStanding"))
		self.ui.pb_finalize_wa.released.connect(lambda: self.finalize("WeaponAssembly"))

		# Kills table add/remove buttons
		self.ui.pb_addwep_cck.released.connect(
			lambda: add_table_field(
				self.fields,
				f"KillsWep",
				self.ui.tb_wep,
				self.ui.box_weapons_cck.currentText(),
				{0: self.ui.box_weapons_cck.currentText()},
				self.ui.box_weapons_cck.currentText(),
			)
		)
		self.ui.pb_removewep_cck.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="KillsWep", table=self.ui.tb_wep
			)
		)
		# self.ui.pb_addtar_cck.released.connect(lambda: self.state.add_table_field(f"KillsTarget", self.ui.tb_targets, self.ui.box_targets_cck.currentText(), {0: self.ui.box_targets_cck.currentText()}, self.ui.box_targets_cck.currentText()))
		# self.ui.pb_removetar_cck.released.connect(lambda: self.state.remove_selected_table_item(type="KillsTarget", table=self.ui.tb_targets))
		self.ui.pb_addtr_cck.released.connect(
			lambda: add_table_field(
				self.fields,
				f"KillsTargetRole",
				self.ui.tb_targetrole,
				self.ui.box_targetrole_cck.currentText(),
				{0: self.ui.box_targetrole_cck.currentText()},
				self.ui.box_targetrole_cck.currentText(),
			)
		)
		self.ui.pb_removetr_cck.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="KillsTargetRole", table=self.ui.tb_targetrole
			)
		)
		self.ui.pb_addbp_cck.released.connect(
			lambda: add_table_field(
				self.fields,
				f"KillsBodyPart",
				self.ui.tb_bodypart,
				self.ui.box_bodypart_cck.currentText(),
				{0: self.ui.box_bodypart_cck.currentText()},
				self.ui.box_bodypart_cck.currentText(),
			)
		)
		self.ui.pb_rembp_cck.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="KillsBodyPart", table=self.ui.tb_bodypart
			)
		)
		self.ui.pb_add_imod.released.connect(
			lambda: add_table_field(
				self.fields,
				f"KillsModInc",
				self.ui.tb_incmods,
				self.ui.fld_incmod_cck.displayText(),
				{0: self.ui.fld_incmod_cck.displayText()},
				self.ui.fld_incmod_cck.displayText(),
			)
		)
		self.ui.pb_rem_imod.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="KillsModInc", table=self.ui.tb_incmods
			)
		)
		self.ui.pb_add_emod.released.connect(
			lambda: add_table_field(
				self.fields,
				f"KillsModExc",
				self.ui.tb_excmods,
				self.ui.fld_excmod_cck.displayText(),
				{0: self.ui.fld_excmod_cck.displayText()},
				self.ui.fld_excmod_cck.displayText(),
			)
		)
		self.ui.pb_rem_emod.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="KillsModExc", table=self.ui.tb_excmods
			)
		)

		# Other table buttons
		self.ui.pb_remove_cc.released.connect(self.remove_selected_subtask)
		self.ui.pb_edit_cc.released.connect(self.edit_selected_subtask)
		self.ui.tb_cc.cellDoubleClicked.connect(lambda row, _column: self.edit_subtask(row))

		self.ui.pb_status_rem_cces.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ExitStatus", table=self.ui.tb_cces
			)
		)
		self.ui.pb_cces_add.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ExitStatus",
				self.ui.tb_cces,
				self.ui.box_status_cces.currentText(),
				{0: self.ui.box_status_cces.currentText()},
				self.ui.box_status_cces.currentText(),
			)
		)

		self.ui.pb_add_ccl.released.connect(
			lambda: add_table_field(
				self.fields,
				f"Location",
				self.ui.tb_ccl,
				self.ui.box_location_ccl.currentText(),
				{0: self.ui.box_location_ccl.currentText()},
				self.ui.box_location_ccl.currentText(),
			)
		)
		self.ui.pb_rem_ccl.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="Location", table=self.ui.tb_ccl
			)
		)

		self.ui.pb_addvis.released.connect(
			lambda: add_table_field(
				self.fields,
				f"VisibilityCond",
				self.ui.tb_vis,
				self.ui.fld_visibility_targetid.displayText(),
				{0: self.ui.fld_visibility_targetid.displayText()},
				self.ui.fld_visibility_targetid.displayText(),
			)
		)
		self.ui.pb_remvis.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="VisibilityCond", table=self.ui.tb_vis
			)
		)

		self.ui.pb_additem_it.released.connect(
			lambda: add_table_field(
				self.fields,
				f"HFItems",
				self.ui.tb_items,
				self.ui.fld_itemid_it.displayText(),
				{0: self.ui.fld_itemid_it.displayText()},
				self.ui.fld_itemid_it.displayText(),
			)
		)
		self.ui.pb_remitem_it.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="HFItems", table=self.ui.tb_items
			)
		)

		self.ui.pb_addstatus_qs.released.connect(
			lambda: add_table_field(
				self.fields,
				f"QStatus",
				self.ui.tb_status_qs,
				self.ui.box_status_qs.currentText(),
				{0: self.ui.box_status_qs.currentText()},
				self.ui.box_status_qs.currentText(),
			)
		)
		self.ui.pb_remstatus_qs.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="QStatus", table=self.ui.tb_status_qs
			)
		)

		self.ui.pb_add_li_target.released.connect(
			lambda: add_table_field(
				self.fields,
				f"LeaveItemTarget",
				self.ui.tb_li_target,
				self.ui.fld_li_target.displayText(),
				{0: self.ui.fld_li_target.displayText()},
				self.ui.fld_li_target.displayText(),
			)
		)
		self.ui.pb_rem_li_target.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="LeaveItemTarget", table=self.ui.tb_li_target
			)
		)

		self.ui.pb_add_eqi.released.connect(
			lambda: add_table_field(
				self.fields,
				f"EquipmentInclusive",
				self.ui.tb_eq_inc,
				self.ui.fld_eqi.displayText(),
				{
					0: self.ui.fld_eqi.displayText(),
					1: self.ui.fld_equi_org.displayText(),
				},
				{
					"id": self.ui.fld_eqi.displayText(),
					"org": self.ui.fld_equi_org.displayText(),
				},
			)
		)
		self.ui.pb_rem_eqi.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="EquipmentInclusive", table=self.ui.tb_eq_inc
			)
		)

		self.ui.pb_add_eqe.released.connect(
			lambda: add_table_field(
				self.fields,
				f"EquipmentExclusive",
				self.ui.tb_eq_exc,
				self.ui.fld_eqi_2.displayText(),
				{
					0: self.ui.fld_eqi_2.displayText(),
					1: self.ui.fld_eqe_org.displayText(),
				},
				{
					"id": self.ui.fld_eqi_2.displayText(),
					"org": self.ui.fld_eqe_org.displayText(),
				},
			)
		)
		self.ui.pb_rem_eqe.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="EquipmentExclusive", table=self.ui.tb_eq_exc
			)
		)

		self.ui.pb_add_shbp.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ShotsBodyPart",
				self.ui.tb_sh_bp,
				self.ui.box_shbp.currentText(),
				{0: self.ui.box_shbp.currentText()},
				self.ui.box_shbp.currentText(),
			)
		)
		self.ui.pb_rem_shbp.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ShotsBodyPart", table=self.ui.tb_sh_bp
			)
		)

		self.ui.pb_add_shtr.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ShotsTargetRole",
				self.ui.tb_sh_tr,
				self.ui.box_shtr.currentText(),
				{0: self.ui.box_shtr.currentText()},
				self.ui.box_shtr.currentText(),
			)
		)
		self.ui.pb_rem_shtr.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ShotsTargetRole", table=self.ui.tb_sh_tr
			)
		)

		self.ui.pb_add_shw.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ShotsWeapon",
				self.ui.tb_sh_wep,
				self.ui.fld_shw.displayText(),
				{0: self.ui.fld_shw.displayText()},
				self.ui.fld_shw.displayText(),
			)
		)
		self.ui.pb_rem_shw.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ShotsWeapon", table=self.ui.tb_sh_wep
			)
		)

		self.ui.pb_add_shmi.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ShotsModsInclusive",
				self.ui.tb_incmod_sh,
				self.ui.fld_shmi.displayText(),
				{0: self.ui.fld_shmi.displayText()},
				self.ui.fld_shmi.displayText(),
			)
		)
		self.ui.pb_rem_shmi.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ShotsModsInclusive", table=self.ui.tb_incmod_sh
			)
		)

		self.ui.pb_add_shme.released.connect(
			lambda: add_table_field(
				self.fields,
				f"ShotsModsExclusive",
				self.ui.tb_excmod_sh,
				self.ui.fld_shme.displayText(),
				{0: self.ui.fld_shme.displayText()},
				self.ui.fld_shme.displayText(),
			)
		)
		self.ui.pb_rem_shme.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="ShotsModsExclusive", table=self.ui.tb_excmod_sh
			)
		)

		self.ui.pb_add_hebp.released.connect(
			lambda: add_table_field(
				self.fields,
				f"HealthEffectBodyPart",
				self.ui.tb_hebp,
				self.ui.box_hebp.currentText(),
				{0: self.ui.box_hebp.currentText()},
				self.ui.box_hebp.currentText(),
			)
		)
		self.ui.pb_rem_hebp.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="HealthEffectBodyPart", table=self.ui.tb_hebp
			)
		)

		self.ui.pb_add_heef.released.connect(
			lambda: add_table_field(
				self.fields,
				f"HealthEffectEffects",
				self.ui.tb_heef,
				self.ui.box_heef.currentText(),
				{0: self.ui.box_heef.currentText()},
				self.ui.box_heef.currentText(),
			)
		)
		self.ui.pb_rem_heef.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="HealthEffectEffects", table=self.ui.tb_heef
			)
		)

		self.ui.pb_add_hb.released.connect(
			lambda: add_table_field(
				self.fields,
				f"HealthBuff",
				self.ui.tb_hb,
				self.ui.box_hb.currentText(),
				{0: self.ui.box_hb.currentText()},
				self.ui.box_hb.currentText(),
			)
		)
		self.ui.pb_rem_hb.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="HealthBuff", table=self.ui.tb_hb
			)
		)

		self.ui.pb_add_iz.released.connect(
			lambda: add_table_field(
				self.fields,
				f"InZone",
				self.ui.tb_iz,
				self.ui.fld_iz.displayText(),
				{0: self.ui.fld_iz.displayText()},
				self.ui.fld_iz.displayText(),
			)
		)
		self.ui.pb_rem_iz.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="InZone", table=self.ui.tb_iz
			)
		)

	def setup_text_edit(self):
		self.ui.fld_taskid_gen.setText(self.id)

	def cc_add(self, cond_type):
		"""Build one CounterCreator sub-condition from the form and add it to the CC table (or, if one of
		this kind is being edited, save the edit)."""
		ui = self.ui
		edit = self.sub_edit if self.sub_edit and self.sub_edit["type"] == cond_type else None
		subtask_id = edit["original"]["id"] if edit else new_id()
		cond = self.build_subcondition(cond_type, subtask_id)
		if edit:
			cond = conditions.edited_subcondition(edit["original"], edit["baseline"], cond)
			self.finish_sub_edit()
		add_table_field(
			self.fields,
			f"CounterCreator",
			ui.tb_cc,
			subtask_id,
			{0: subtask_id, 1: cond_type},
			cond,
		)

	def build_subcondition(self, cond_type, subtask_id):
		"""What the form of a kind of sub-condition describes."""
		ui = self.ui
		state = self.state
		match cond_type:
			case "VisitPlace":
				cond = conditions.visit_place(subtask_id, ui.fld_zoneid_ccvp.displayText())
			case "Kills":
				cond = conditions.kills(
					subtask_id,
					weapon_ids=[
						self.weapon_ids[wep]
						for wep in self.fields.get_singlecolumn_field_list("KillsWep")
					],
					target=(
						ui.box_targets_cck.currentText()
						if ui.chk_cck_usetarget.isChecked()
						else ""
					),
					target_roles=self.fields.get_singlecolumn_field_list("KillsTargetRole"),
					body_parts=self.fields.get_singlecolumn_field_list("KillsBodyPart"),
					mods_inclusive=self.fields.get_singlecolumn_field_list("KillsModInc"),
					mods_exclusive=self.fields.get_singlecolumn_field_list("KillsModExc"),
					distance=val_field(ui.fld_dist_cck.displayText(), "", 0, int),
					distance_compare=ui.box_dist_compare_cck.currentText(),
					time_from=val_field(ui.fld_time_from_cck.displayText(), "", 0, int),
					time_to=val_field(ui.fld_time_to_cck.displayText(), "", 0, int),
					reset_on_session_end=ui.chk_cck_reset_sessionend.isChecked(),
				)
			case "ExitStatus":
				cond = conditions.exit_status(
					subtask_id, self.fields.get_singlecolumn_field_list("ExitStatus")
				)
			case "ExitName":
				cond = conditions.exit_name(subtask_id, ui.fld_exitname_ccen.displayText())
			case "Location":
				cond = conditions.location(
					subtask_id, self.fields.get_singlecolumn_field_list("Location")
				)
			case "Equipment":
				cond = conditions.equipment(
					subtask_id,
					inclusive=self.fields.get_multicolumn_values_list("EquipmentInclusive"),
					exclusive=self.fields.get_multicolumn_values_list("EquipmentExclusive"),
					include_not_equipped=ui.cb_eq_uneq.isChecked(),
				)
			case "Shots":
				cond = conditions.shots(
					subtask_id,
					weapon_ids=self.fields.get_singlecolumn_field_list("ShotsWeapon"),
					body_parts=self.fields.get_singlecolumn_field_list("ShotsBodyPart"),
					target_roles=self.fields.get_singlecolumn_field_list("ShotsTargetRole"),
					mods_inclusive=self.fields.get_singlecolumn_field_list("ShotsModsInclusive"),
					mods_exclusive=self.fields.get_singlecolumn_field_list("ShotsModsExclusive"),
					distance=val_field(ui.fld_dist_sh.displayText(), "", 0, int),
					distance_compare=ui.box_distcomp_sh.currentText(),
					time_from=val_field(ui.fld_timefrom_sh.displayText(), "", 0, int),
					time_to=val_field(ui.fld_timeto_sh.displayText(), "", 0, int),
					value=val_field(ui.fld_value_sh.displayText(), "", 0, int),
					target=ui.box_target_sh.currentText(),
					reset_on_session_end=ui.chk_cck_reset_sessionend_2.isChecked(),
				)
			case "HealthEffect":
				cond = conditions.health_effect(
					subtask_id,
					body_parts=self.fields.get_singlecolumn_field_list("HealthEffectBodyPart"),
					effects=self.fields.get_singlecolumn_field_list("HealthEffectEffects"),
					energy=val_field(ui.fld_enval_he.displayText(), "", 0, int),
					energy_compare=ui.box_encomp_he.currentText(),
					hydration=val_field(ui.fld_hydval_he.displayText(), "", 0, int),
					hydration_compare=ui.box_hydcomp_he.currentText(),
					time=val_field(ui.fld_timeval_he.displayText(), "", 0, int),
					time_compare=ui.box_timecomp_he.currentText(),
				)
			case "HealthBuff":
				cond = conditions.health_buff(
					subtask_id, self.fields.get_singlecolumn_field_list("HealthBuff")
				)
			case "LaunchFlare":
				cond = conditions.launch_flare(subtask_id, ui.fld_fl_zone.displayText())
			case "InZone":
				cond = conditions.in_zone(
					subtask_id, self.fields.get_singlecolumn_field_list("InZone")
				)

		return cond

	def finalize(self, cond_type):
		"""Build the top-level condition from the form and hand it to the quest window."""
		timing, cond = self.build_condition(cond_type)
		if self.editing:
			cond = conditions.edited_condition(self.original, self.baseline, cond)
		self.condition_ready.emit(timing, cond_type, self.id, cond)
		self.close()

	def build_condition(self, cond_type):
		"""What the form describes, as (timing, condition)."""
		ui = self.ui
		state = self.state
		vis = [self.visibility_object(target) for target in self.fields.get_singlecolumn_field_list("VisibilityCond")]
		match cond_type:
			case "CounterCreator":
				timing = ui.box_ff.currentText()
				cond = conditions.counter_creator(
					self.id,
					counter_id=new_id(),
					sub_conditions=self.fields.get_multicolumn_values_list("CounterCreator"),
					parent_id=ui.fld_parentid_cc.displayText(),
					quest_type=ui.box_cc_qtlab.currentText(),
					value=val_field(ui.fld_quantity_cc.displayText(), "", 0, int),
					visibility_conditions=vis,
				)
			case "Item":
				timing = ui.box_ff_it.currentText()
				sub_cond_type = ui.box_hofind_it.currentText()
				if sub_cond_type == "FindItem":
					build_item_condition = conditions.find_item
				elif sub_cond_type == "HandoverItem":
					build_item_condition = conditions.handover_item
				else:
					raise ValueError(f"Unknown item condition type: {sub_cond_type}")
				cond = build_item_condition(
					self.id,
					parent_id=ui.fld_parentid_it.displayText(),
					targets=self.fields.get_singlecolumn_field_list("HFItems"),
					value=val_field(ui.fld_quantity_it.displayText(), "", 0, int),
					min_durability=val_field(ui.fld_mindur_it.displayText(), "", 0, int),
					max_durability=val_field(ui.fld_maxdur_it.displayText(), "", 100, int),
					only_found_in_raid=is_true(ui.box_only_fir_it.currentText()),
					visibility_conditions=vis,
				)
			case "Skill":
				timing = ui.box_ff_sk.currentText()
				cond = conditions.skill(
					self.id,
					compare_method=ui.box_compare_sk.currentText(),
					parent_id=ui.fld_parentid_sk_2.displayText(),
					target=ui.box_target_sk.currentText(),
					value=val_field(ui.fld_level_sk.displayText(), "", 0, int),
					visibility_conditions=vis,
				)
			case "LeaveItemAtLocation":
				timing = ui.box_ff_li.currentText()
				cond = conditions.leave_item_at_location(
					self.id,
					parent_id=ui.fld_parentid_li.displayText(),
					targets=self.fields.get_singlecolumn_field_list("LeaveItemTarget"),
					value=val_field(ui.fld_quantity_li.displayText(), "", 0, int),
					plant_time=val_field(ui.fld_plant_time_li.displayText(), "", 0, int),
					min_durability=val_field(ui.fld_mindur_li.displayText(), "", 0, int),
					max_durability=val_field(ui.fld_maxdur_li.displayText(), "", 100, int),
					only_found_in_raid=is_true(ui.box_fir_li.currentText()),
					zone_id=ui.fld_zoneid_li.displayText(),
					visibility_conditions=vis,
				)
			case "PlaceBeacon":
				timing = ui.box_ff_pb.currentText()
				cond = conditions.place_beacon(
					self.id,
					parent_id=ui.fld_parentid_pb.displayText(),
					plant_time=val_field(ui.sb_time_pb.cleanText(), "", 10, int),
					value=val_field(ui.sb_value_pb.cleanText(), "", 1, int),
					zone_id=ui.fld_zoneid_pb.displayText(),
					visibility_conditions=vis,
				)
			case "WeaponAssembly":
				timing = "Finish"
				cond = conditions.weapon_assembly()
			case "TraderLoyalty":
				timing = ui.box_ff_tl.currentText()
				cond = conditions.trader_loyalty(
					self.id,
					compare_method=ui.box_compare_tl.currentText(),
					parent_id=ui.fld_parentid_tl.displayText(),
					trader_id=self.trader_ids[ui.box_target_tl.currentText()],
					value=val_field(ui.fld_level_tl.displayText(), "", 0, int),
					visibility_conditions=vis,
				)

			# These 3 next are start-only
			case "Level":
				timing = self.fixed_timing
				cond = conditions.level(
					self.id,
					compare_method=ui.box_compare_lv.currentText(),
					value=val_field(ui.fld_value_lv.displayText(), "", 0, int),
				)
			case "Quest":
				timing = ui.box_timing_qs.currentText()
				cond = conditions.quest_status(
					self.id,
					available_after=val_field(ui.fld_avail_qs.displayText(), "", 0, int),
					status_ids=[
						self.status_ids[s] for s in self.fields.get_singlecolumn_field_list("QStatus")
					],
					target=ui.fld_tid_qs.displayText(),
				)
			case "TraderStanding":
				timing = self.fixed_timing
				cond = conditions.trader_standing(
					self.id,
					compare_method=ui.box_comparemethod_ts.currentText(),
					trader_id=self.trader_ids[ui.box_trader_ts.currentText()],
					value=val_field(ui.fld_value_ts.displayText(), "", 0, int),
				)

		return timing, cond

	def visibility_object(self, target):
		"""The visibility condition for a target: the one the task already had, or else one with a new
		id (made once, so building the task again gives the same one)."""
		if target not in self.visibility_objects:
			for entry in (self.original or {}).get("visibilityConditions", []):
				if isinstance(entry, dict) and entry.get("target") == target:
					self.visibility_objects[target] = copy.deepcopy(entry)
					break
			else:
				self.visibility_objects[target] = conditions.visibility_condition(new_id(), target)
		return copy.deepcopy(self.visibility_objects[target])

	# --- editing an existing task -----------------------------------------------------------

	@property
	def editing(self):
		"""Whether this dialog edits an existing task (rather than making a new one)."""
		return self.original is not None

	def load_condition(self, cond, timing):
		"""Fill the form of the task's kind from the condition, and leave only that kind's tab usable."""
		ui = self.ui
		kind = dialog_type(cond)
		self.setWindowTitle("Edit Task")
		for tabs_name, page_name in TASK_TABS[kind]:
			tabs, page = getattr(ui, tabs_name), getattr(ui, page_name)
			for index in range(tabs.count()):
				tabs.setTabEnabled(index, tabs.widget(index) is page)
			tabs.setCurrentWidget(page)
		getattr(ui, FINISH_BUTTONS[kind]).setText("Save Changes")
		getattr(self, f"load_{cond['conditionType']}")(cond, timing)
		if cond["conditionType"] in ("FindItem", "HandoverItem", "LeaveItemAtLocation", "Skill", "CounterCreator", "PlaceBeacon", "TraderLoyalty"):
			for entry in cond.get("visibilityConditions", []):
				target = visibility_target(entry)
				add_table_field(self.fields, "VisibilityCond", ui.tb_vis, target, {0: target}, target)
		self.baseline = self.build_condition(kind)[1]

	# --- editing a Counter's sub-conditions ---------------------------------------------------

	def edit_selected_subtask(self):
		"""The Edit Selected Subtask button."""
		selected = self.ui.tb_cc.selectedItems()
		if selected:
			self.edit_subtask(selected[0].row())

	def edit_subtask(self, row):
		"""Load the sub-condition in a row of the Counter's table into its form, to edit it there; pressing
		the form's button (now "Save Subtask") saves it. Returns whether it was loaded."""
		table = self.ui.tb_cc
		if table.item(row, 0) is None:
			return False
		sub = self.fields.data.get("CounterCreator", {}).get(table.item(row, 0).text())
		if sub is None:
			return False
		if not can_edit_subcondition(sub):
			QMessageBox.information(
				self,
				"Edit Subtask",
				f"The Task Builder can't make subtasks of type {sub.get('conditionType')}, so it can't edit "
				"this one either.\n\nYou can remove it, or leave it as it is.",
			)
			return False
		self.finish_sub_edit()  # (an edit that was started and never saved is dropped)
		kind = sub["conditionType"]
		sub = copy.deepcopy(sub)
		getattr(self, f"load_sub_{kind}")(sub)
		self.ui.tabWidget_4.setCurrentWidget(getattr(self.ui, SUB_TABS[kind]))
		button = getattr(self.ui, SUB_BUTTONS[kind])
		self.sub_edit = {"original": sub, "type": kind, "text": button.text(), "baseline": self.build_subcondition(kind, sub["id"])}
		button.setText("Save Subtask")
		return True

	def finish_sub_edit(self):
		"""Stop editing a sub-condition (its button goes back to what it said)."""
		if self.sub_edit is not None:
			getattr(self.ui, SUB_BUTTONS[self.sub_edit["type"]]).setText(self.sub_edit["text"])
			self.sub_edit = None

	def remove_selected_subtask(self):
		selected = self.ui.tb_cc.selectedItems()
		if selected and self.sub_edit is not None:
			if self.ui.tb_cc.item(selected[0].row(), 0).text() == self.sub_edit["original"]["id"]:
				self.finish_sub_edit()  # (saving it would bring the removed subtask back)
		remove_selected_table_item(self.fields, type="CounterCreator", table=self.ui.tb_cc)

	def refill(self, field_type, table, values):
		"""Replace the rows of one of the form's tables with these values."""
		self.fields.data.pop(field_type, None)
		table.setRowCount(0)
		for value in values:
			add_table_field(self.fields, field_type, table, value, {0: value}, value)

	def refill_equipment(self, field_type, table, groups):
		self.fields.data.pop(field_type, None)
		table.setRowCount(0)
		for number, group in enumerate(groups or [], 1):
			for item_id in group:
				add_table_field(
					self.fields, field_type, table, item_id, {0: item_id, 1: str(number)}, {"id": item_id, "org": str(number)}
				)

	def weapon_names(self, ids):
		"""The names the Kills form shows for weapon ids (an id it has no name for is shown as itself)."""
		names = {weapon_id: name for name, weapon_id in self.weapon_ids.items()}
		out = []
		for weapon_id in ids:
			if weapon_id not in names:
				names[weapon_id] = weapon_id
				self.weapon_ids[weapon_id] = weapon_id
			out.append(names[weapon_id])
		return out

	def load_sub_VisitPlace(self, sub):
		self.set_text(self.ui.fld_zoneid_ccvp, sub.get("target", ""))

	def load_sub_ExitStatus(self, sub):
		self.refill("ExitStatus", self.ui.tb_cces, sub.get("status", []))

	def load_sub_ExitName(self, sub):
		self.set_text(self.ui.fld_exitname_ccen, sub.get("exitName", ""))

	def load_sub_Location(self, sub):
		self.refill("Location", self.ui.tb_ccl, sub.get("target", []))

	def load_sub_LaunchFlare(self, sub):
		self.set_text(self.ui.fld_fl_zone, sub.get("target", ""))

	def load_sub_InZone(self, sub):
		self.refill("InZone", self.ui.tb_iz, sub.get("zoneIds", []))

	def load_sub_HealthBuff(self, sub):
		self.refill("HealthBuff", self.ui.tb_hb, sub.get("target", []))

	def load_sub_Equipment(self, sub):
		ui = self.ui
		ui.cb_eq_uneq.setChecked(bool(sub.get("IncludeNotEquippedItems", False)))
		self.refill_equipment("EquipmentInclusive", ui.tb_eq_inc, sub.get("equipmentInclusive", []))
		self.refill_equipment("EquipmentExclusive", ui.tb_eq_exc, sub.get("equipmentExclusive", []))

	def load_sub_HealthEffect(self, sub):
		ui = self.ui
		group = (sub.get("bodyPartsWithEffects") or [{}])[0]  # (the form holds one group of body parts and effects)
		self.refill("HealthEffectBodyPart", ui.tb_hebp, group.get("bodyParts", []))
		self.refill("HealthEffectEffects", ui.tb_heef, group.get("effects", []))
		for key, field, box in (
			("energy", ui.fld_enval_he, ui.box_encomp_he),
			("hydration", ui.fld_hydval_he, ui.box_hydcomp_he),
			("time", ui.fld_timeval_he, ui.box_timecomp_he),
		):
			setting = sub.get(key, {})
			self.set_text(field, setting.get("value", 0))
			select_or_add(box, setting.get("compareMethod", ">="))

	def load_sub_Kills(self, sub):
		ui = self.ui
		self.refill("KillsWep", ui.tb_wep, self.weapon_names(sub.get("weapon", [])))
		self.refill("KillsTargetRole", ui.tb_targetrole, sub.get("savageRole", []))
		self.refill("KillsBodyPart", ui.tb_bodypart, sub.get("bodyPart", []))
		self.refill("KillsModInc", ui.tb_incmods, flat(sub.get("weaponModsInclusive")))
		self.refill("KillsModExc", ui.tb_excmods, flat(sub.get("weaponModsExclusive")))
		target = sub.get("target", "")
		ui.chk_cck_usetarget.setChecked(bool(target))
		if target:
			select_or_add(ui.box_targets_cck, str(target))
		distance = sub.get("distance", {})
		self.set_text(ui.fld_dist_cck, distance.get("value", 0))
		select_or_add(ui.box_dist_compare_cck, distance.get("compareMethod", ">="))
		daytime = sub.get("daytime", {})
		self.set_text(ui.fld_time_from_cck, daytime.get("from", 0))
		self.set_text(ui.fld_time_to_cck, daytime.get("to", 0))
		ui.chk_cck_reset_sessionend.setChecked(bool(sub.get("resetOnSessionEnd", False)))

	def load_sub_Shots(self, sub):
		ui = self.ui
		self.refill("ShotsWeapon", ui.tb_sh_wep, sub.get("weapon", []))
		self.refill("ShotsTargetRole", ui.tb_sh_tr, sub.get("savageRole", []))
		self.refill("ShotsBodyPart", ui.tb_sh_bp, sub.get("bodyPart", []))
		self.refill("ShotsModsInclusive", ui.tb_incmod_sh, flat(sub.get("weaponModsInclusive")))
		self.refill("ShotsModsExclusive", ui.tb_excmod_sh, flat(sub.get("weaponModsExclusive")))
		select_or_add(ui.box_target_sh, str(sub.get("target", "Any")))
		distance = sub.get("distance", {})
		self.set_text(ui.fld_dist_sh, distance.get("value", 0))
		select_or_add(ui.box_distcomp_sh, distance.get("compareMethod", ">="))
		daytime = sub.get("daytime", {})
		self.set_text(ui.fld_timefrom_sh, daytime.get("from", 0))
		self.set_text(ui.fld_timeto_sh, daytime.get("to", 0))
		self.set_text(ui.fld_value_sh, sub.get("value", 0))
		ui.chk_cck_reset_sessionend_2.setChecked(bool(sub.get("resetOnSessionEnd", False)))

	def set_text(self, field, value):
		field.setText("" if value is None else str(value))

	def load_targets(self, field_type, table, values):
		for value in values:
			add_table_field(self.fields, field_type, table, value, {0: value}, value)

	def load_CounterCreator(self, cond, timing):
		ui = self.ui
		self.set_text(ui.fld_parentid_cc, cond.get("parentId", ""))
		select_or_add(ui.box_cc_qtlab, str(cond.get("type", "")))
		self.set_text(ui.fld_quantity_cc, cond.get("value", 0))
		select_or_add(ui.box_ff, timing or "Finish")
		for sub in copy.deepcopy(cond.get("counter", {}).get("conditions", [])):
			add_table_field(
				self.fields, "CounterCreator", ui.tb_cc, sub["id"], {0: sub["id"], 1: sub.get("conditionType", "")}, sub
			)

	def load_item_condition(self, cond, timing):
		ui = self.ui
		select_or_add(ui.box_hofind_it, cond["conditionType"])
		ui.box_hofind_it.setEnabled(False)  # (turning one into the other would change what the task is)
		self.set_text(ui.fld_parentid_it, cond.get("parentId", ""))
		self.load_targets("HFItems", ui.tb_items, cond.get("target", []))
		self.set_text(ui.fld_quantity_it, cond.get("value", 0))
		self.set_text(ui.fld_mindur_it, cond.get("minDurability", 0))
		self.set_text(ui.fld_maxdur_it, cond.get("maxDurability", 100))
		select_or_add(ui.box_only_fir_it, str(bool(cond.get("onlyFoundInRaid", False))).lower())
		select_or_add(ui.box_ff_it, timing or "Finish")

	def load_FindItem(self, cond, timing):
		self.load_item_condition(cond, timing)

	def load_HandoverItem(self, cond, timing):
		self.load_item_condition(cond, timing)

	def load_Skill(self, cond, timing):
		ui = self.ui
		select_or_add(ui.box_compare_sk, cond.get("compareMethod", ">="))
		self.set_text(ui.fld_parentid_sk_2, cond.get("parentId", ""))
		select_or_add(ui.box_target_sk, str(cond.get("target", "")))
		self.set_text(ui.fld_level_sk, cond.get("value", 0))
		select_or_add(ui.box_ff_sk, timing or "Finish")

	def load_LeaveItemAtLocation(self, cond, timing):
		ui = self.ui
		self.set_text(ui.fld_parentid_li, cond.get("parentId", ""))
		self.load_targets("LeaveItemTarget", ui.tb_li_target, cond.get("target", []))
		self.set_text(ui.fld_quantity_li, cond.get("value", 0))
		self.set_text(ui.fld_plant_time_li, cond.get("plantTime", 0))
		self.set_text(ui.fld_mindur_li, cond.get("minDurability", 0))
		self.set_text(ui.fld_maxdur_li, cond.get("maxDurability", 100))
		select_or_add(ui.box_fir_li, str(bool(cond.get("onlyFoundInRaid", False))).lower())
		self.set_text(ui.fld_zoneid_li, cond.get("zoneId", ""))
		select_or_add(ui.box_ff_li, timing or "Finish")

	def load_PlaceBeacon(self, cond, timing):
		ui = self.ui
		self.set_text(ui.fld_parentid_pb, cond.get("parentId", ""))
		ui.sb_time_pb.setValue(self.whole_number(cond.get("plantTime", 10)))
		ui.sb_value_pb.setValue(self.whole_number(cond.get("value", 1)))
		self.set_text(ui.fld_zoneid_pb, cond.get("zoneId", ""))
		select_or_add(ui.box_ff_pb, timing or "Finish")

	def load_TraderLoyalty(self, cond, timing):
		ui = self.ui
		select_or_add(ui.box_compare_tl, cond.get("compareMethod", ">="))
		self.set_text(ui.fld_parentid_tl, cond.get("parentId", ""))
		select_id(ui.box_target_tl, self.trader_ids, cond.get("target", ""))
		self.set_text(ui.fld_level_tl, cond.get("value", 0))
		select_or_add(ui.box_ff_tl, timing or "Finish")  # (some vanilla ones are Start conditions)

	def load_Level(self, cond, timing):
		ui = self.ui
		select_or_add(ui.box_compare_lv, cond.get("compareMethod", ">="))
		self.set_text(ui.fld_value_lv, cond.get("value", 0))

	def load_Quest(self, cond, timing):
		ui = self.ui
		self.set_text(ui.fld_tid_qs, cond.get("target", ""))
		self.set_text(ui.fld_avail_qs, cond.get("availableAfter", 0))
		select_or_add(ui.box_timing_qs, timing or "Start")
		names = {code: name for name, code in self.status_ids.items()}
		for code in cond.get("status", []):
			try:
				name = names.get(int(code))
			except (TypeError, ValueError):
				name = None
			if name is None:
				name = str(code)
				self.status_ids[name] = code
			self.load_targets("QStatus", ui.tb_status_qs, [name])

	def load_TraderStanding(self, cond, timing):
		ui = self.ui
		select_or_add(ui.box_comparemethod_ts, cond.get("compareMethod", ">="))
		select_id(ui.box_trader_ts, self.trader_ids, cond.get("target", ""))
		self.set_text(ui.fld_value_ts, cond.get("value", 0))

	@staticmethod
	def whole_number(value):
		"""A number for a spin box (a number written as text works too)."""
		try:
			return int(float(value))
		except (TypeError, ValueError):
			return 0
