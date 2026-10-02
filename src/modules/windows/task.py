from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from modules.builders import conditions
from modules.gui.compiled.gui_tasks import Ui_TaskWindow
from modules.state import TableFields
from modules.table_fields import add_table_field, remove_selected_table_item
from modules.utils import is_true, new_id, val_field


class Gui_TaskDlg(QMainWindow):
	# (timing, condition_type, condition_id, condition) - sent when the user finalizes a condition
	condition_ready = Signal(str, str, str, object)

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_TaskWindow()
		self.ui.setupUi(self)
		self.state = state
		self.fields = TableFields()  # this dialog's own table rows
		self.id = new_id()
		self.cc = []
		# self.weapons = [] # used for CC/Kills, add ids in as needed
		# self.status = [] # used for CC/exitstatus
		# self.location = [] # used for cc/location
		self.on_launch()  # Custom code in this one
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
		self.ui.pb_remove_cc.released.connect(
			lambda: remove_selected_table_item(
				self.fields,
				type="CounterCreator", table=self.ui.tb_cc
			)
		)

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
		"""Build one CounterCreator sub-condition from the form and add it to the CC table."""
		ui = self.ui
		state = self.state
		subtask_id = new_id()
		match cond_type:
			case "VisitPlace":
				cond = conditions.visit_place(subtask_id, ui.fld_zoneid_ccvp.displayText())
			case "Kills":
				cond = conditions.kills(
					subtask_id,
					weapon_ids=[
						state.weapons[wep]
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

		add_table_field(
			self.fields,
			f"CounterCreator",
			ui.tb_cc,
			subtask_id,
			{0: subtask_id, 1: cond_type},
			cond,
		)

	def finalize(self, cond_type):
		"""Build the top-level condition from the form and hand it to the quest window."""
		ui = self.ui
		state = self.state
		vis = [
			conditions.visibility_condition(new_id(), target)
			for target in self.fields.get_singlecolumn_field_list("VisibilityCond")
		]
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
					trader_id=state.traders[ui.box_target_tl.currentText()],
					value=val_field(ui.fld_level_tl.displayText(), "", 0, int),
					visibility_conditions=vis,
				)

			# These 3 next are start-only
			case "Level":
				timing = "Start"
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
						state.status[s] for s in self.fields.get_singlecolumn_field_list("QStatus")
					],
					target=ui.fld_tid_qs.displayText(),
				)
			case "TraderStanding":
				timing = "Start"
				cond = conditions.trader_standing(
					self.id,
					compare_method=ui.box_comparemethod_ts.currentText(),
					trader_id=state.traders[ui.box_trader_ts.currentText()],
					value=val_field(ui.fld_value_ts.displayText(), "", 0, int),
				)

		self.condition_ready.emit(timing, cond_type, self.id, cond)
		self.close()
