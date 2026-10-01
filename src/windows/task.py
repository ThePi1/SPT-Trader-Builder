from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow

from tb_ui.gui_tasks import Ui_TaskWindow
from table_fields import add_table_field, remove_selected_table_item
from utils import is_true, new_id, val_field


class Gui_TaskDlg(QMainWindow):
	# (timing, condition_type, condition_id, condition) - sent when the user finalizes a condition
	condition_ready = Signal(str, str, str, object)

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.ui = Ui_TaskWindow()
		self.ui.setupUi(self)
		self.state = state
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
				self.state,
				f"KillsWep",
				self.ui.tb_wep,
				self.ui.box_weapons_cck.currentText(),
				{0: self.ui.box_weapons_cck.currentText()},
				self.ui.box_weapons_cck.currentText(),
			)
		)
		self.ui.pb_removewep_cck.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="KillsWep", table=self.ui.tb_wep
			)
		)
		# self.ui.pb_addtar_cck.released.connect(lambda: self.state.add_table_field(f"KillsTarget", self.ui.tb_targets, self.ui.box_targets_cck.currentText(), {0: self.ui.box_targets_cck.currentText()}, self.ui.box_targets_cck.currentText()))
		# self.ui.pb_removetar_cck.released.connect(lambda: self.state.remove_selected_table_item(type="KillsTarget", table=self.ui.tb_targets))
		self.ui.pb_addtr_cck.released.connect(
			lambda: add_table_field(
				self.state,
				f"KillsTargetRole",
				self.ui.tb_targetrole,
				self.ui.box_targetrole_cck.currentText(),
				{0: self.ui.box_targetrole_cck.currentText()},
				self.ui.box_targetrole_cck.currentText(),
			)
		)
		self.ui.pb_removetr_cck.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="KillsTargetRole", table=self.ui.tb_targetrole
			)
		)
		self.ui.pb_addbp_cck.released.connect(
			lambda: add_table_field(
				self.state,
				f"KillsBodyPart",
				self.ui.tb_bodypart,
				self.ui.box_bodypart_cck.currentText(),
				{0: self.ui.box_bodypart_cck.currentText()},
				self.ui.box_bodypart_cck.currentText(),
			)
		)
		self.ui.pb_rembp_cck.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="KillsBodyPart", table=self.ui.tb_bodypart
			)
		)
		self.ui.pb_add_imod.released.connect(
			lambda: add_table_field(
				self.state,
				f"KillsModInc",
				self.ui.tb_incmods,
				self.ui.fld_incmod_cck.displayText(),
				{0: self.ui.fld_incmod_cck.displayText()},
				self.ui.fld_incmod_cck.displayText(),
			)
		)
		self.ui.pb_rem_imod.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="KillsModInc", table=self.ui.tb_incmods
			)
		)
		self.ui.pb_add_emod.released.connect(
			lambda: add_table_field(
				self.state,
				f"KillsModExc",
				self.ui.tb_excmods,
				self.ui.fld_excmod_cck.displayText(),
				{0: self.ui.fld_excmod_cck.displayText()},
				self.ui.fld_excmod_cck.displayText(),
			)
		)
		self.ui.pb_rem_emod.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="KillsExc", table=self.ui.tb_excmods
			)
		)

		# Other table buttons
		self.ui.pb_remove_cc.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="CounterCreator", table=self.ui.tb_cc
			)
		)

		self.ui.pb_status_rem_cces.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ExitStatus", table=self.ui.tb_cces
			)
		)
		self.ui.pb_cces_add.released.connect(
			lambda: add_table_field(
				self.state,
				f"ExitStatus",
				self.ui.tb_cces,
				self.ui.box_status_cces.currentText(),
				{0: self.ui.box_status_cces.currentText()},
				self.ui.box_status_cces.currentText(),
			)
		)

		self.ui.pb_add_ccl.released.connect(
			lambda: add_table_field(
				self.state,
				f"Location",
				self.ui.tb_ccl,
				self.ui.box_location_ccl.currentText(),
				{0: self.ui.box_location_ccl.currentText()},
				self.ui.box_location_ccl.currentText(),
			)
		)
		self.ui.pb_rem_ccl.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="Location", table=self.ui.tb_ccl
			)
		)

		self.ui.pb_addvis.released.connect(
			lambda: add_table_field(
				self.state,
				f"VisibilityCond",
				self.ui.tb_vis,
				self.ui.fld_visibility_targetid.displayText(),
				{0: self.ui.fld_visibility_targetid.displayText()},
				self.ui.fld_visibility_targetid.displayText(),
			)
		)
		self.ui.pb_remvis.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="VisibilityCond", table=self.ui.tb_vis
			)
		)

		self.ui.pb_additem_it.released.connect(
			lambda: add_table_field(
				self.state,
				f"HFItems",
				self.ui.tb_items,
				self.ui.fld_itemid_it.displayText(),
				{0: self.ui.fld_itemid_it.displayText()},
				self.ui.fld_itemid_it.displayText(),
			)
		)
		self.ui.pb_remitem_it.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="HFItems", table=self.ui.tb_items
			)
		)

		self.ui.pb_addstatus_qs.released.connect(
			lambda: add_table_field(
				self.state,
				f"QStatus",
				self.ui.tb_status_qs,
				self.ui.box_status_qs.currentText(),
				{0: self.ui.box_status_qs.currentText()},
				self.ui.box_status_qs.currentText(),
			)
		)
		self.ui.pb_remstatus_qs.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="QStatus", table=self.ui.tb_status_qs
			)
		)

		self.ui.pb_add_li_target.released.connect(
			lambda: add_table_field(
				self.state,
				f"LeaveItemTarget",
				self.ui.tb_li_target,
				self.ui.fld_li_target.displayText(),
				{0: self.ui.fld_li_target.displayText()},
				self.ui.fld_li_target.displayText(),
			)
		)
		self.ui.pb_rem_li_target.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="LeaveItemTarget", table=self.ui.tb_li_target
			)
		)

		self.ui.pb_add_eqi.released.connect(
			lambda: add_table_field(
				self.state,
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
				self.state,
				type="EquipmentInclusive", table=self.ui.tb_eq_inc
			)
		)

		self.ui.pb_add_eqe.released.connect(
			lambda: add_table_field(
				self.state,
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
				self.state,
				type="EquipmentExclusive", table=self.ui.tb_eq_exc
			)
		)

		self.ui.pb_add_shbp.released.connect(
			lambda: add_table_field(
				self.state,
				f"ShotsBodyPart",
				self.ui.tb_sh_bp,
				self.ui.box_shbp.currentText(),
				{0: self.ui.box_shbp.currentText()},
				self.ui.box_shbp.currentText(),
			)
		)
		self.ui.pb_rem_shbp.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ShotsBodyPart", table=self.ui.tb_sh_bp
			)
		)

		self.ui.pb_add_shtr.released.connect(
			lambda: add_table_field(
				self.state,
				f"ShotsTargetRole",
				self.ui.tb_sh_tr,
				self.ui.box_shtr.currentText(),
				{0: self.ui.box_shtr.currentText()},
				self.ui.box_shtr.currentText(),
			)
		)
		self.ui.pb_rem_shtr.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ShotsTargetRole", table=self.ui.tb_sh_tr
			)
		)

		self.ui.pb_add_shw.released.connect(
			lambda: add_table_field(
				self.state,
				f"ShotsWeapon",
				self.ui.tb_sh_wep,
				self.ui.fld_shw.displayText(),
				{0: self.ui.fld_shw.displayText()},
				self.ui.fld_shw.displayText(),
			)
		)
		self.ui.pb_rem_shw.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ShotsWeapon", table=self.ui.tb_sh_wep
			)
		)

		self.ui.pb_add_shmi.released.connect(
			lambda: add_table_field(
				self.state,
				f"ShotsModsInclusive",
				self.ui.tb_incmod_sh,
				self.ui.fld_shmi.displayText(),
				{0: self.ui.fld_shmi.displayText()},
				self.ui.fld_shmi.displayText(),
			)
		)
		self.ui.pb_rem_shmi.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ShotsModsInclusive", table=self.ui.tb_incmod_sh
			)
		)

		self.ui.pb_add_shme.released.connect(
			lambda: add_table_field(
				self.state,
				f"ShotsModsExclusive",
				self.ui.tb_excmod_sh,
				self.ui.fld_shme.displayText(),
				{0: self.ui.fld_shme.displayText()},
				self.ui.fld_shme.displayText(),
			)
		)
		self.ui.pb_rem_shme.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="ShotsModsExclusive", table=self.ui.tb_excmod_sh
			)
		)

		self.ui.pb_add_hebp.released.connect(
			lambda: add_table_field(
				self.state,
				f"HealthEffectBodyPart",
				self.ui.tb_hebp,
				self.ui.box_hebp.currentText(),
				{0: self.ui.box_hebp.currentText()},
				self.ui.box_hebp.currentText(),
			)
		)
		self.ui.pb_rem_hebp.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="HealthEffectBodyPart", table=self.ui.tb_hebp
			)
		)

		self.ui.pb_add_heef.released.connect(
			lambda: add_table_field(
				self.state,
				f"HealthEffectEffects",
				self.ui.tb_heef,
				self.ui.box_heef.currentText(),
				{0: self.ui.box_heef.currentText()},
				self.ui.box_heef.currentText(),
			)
		)
		self.ui.pb_rem_heef.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="HealthEffectEffects", table=self.ui.tb_heef
			)
		)

		self.ui.pb_add_hb.released.connect(
			lambda: add_table_field(
				self.state,
				f"HealthBuff",
				self.ui.tb_hb,
				self.ui.box_hb.currentText(),
				{0: self.ui.box_hb.currentText()},
				self.ui.box_hb.currentText(),
			)
		)
		self.ui.pb_rem_hb.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="HealthBuff", table=self.ui.tb_hb
			)
		)

		self.ui.pb_add_iz.released.connect(
			lambda: add_table_field(
				self.state,
				f"InZone",
				self.ui.tb_iz,
				self.ui.fld_iz.displayText(),
				{0: self.ui.fld_iz.displayText()},
				self.ui.fld_iz.displayText(),
			)
		)
		self.ui.pb_rem_iz.released.connect(
			lambda: remove_selected_table_item(
				self.state,
				type="InZone", table=self.ui.tb_iz
			)
		)

	def setup_text_edit(self):
		self.ui.fld_taskid_gen.setText(self.id)

	def cc_add(self, cond_type):
		subtask_id = new_id()
		match cond_type:
			case "VisitPlace":
				cond = {
					"conditionType": "VisitPlace",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": subtask_id,
					"target": self.ui.fld_zoneid_ccvp.displayText(),
					"value": 1,
				}
			case "Kills":
				local_weapons = self.state.get_singlecolumn_field_list(
					"KillsWep"
				)
				local_weapons_id = []
				for wep in local_weapons:
					local_weapons_id.append(self.state.weapons[wep])
				# local_targets = self.state.get_singlecolumn_field_list("KillsTarget")
				if self.ui.chk_cck_usetarget.isChecked():
					local_targets = self.ui.box_targets_cck.currentText()
				else:
					local_targets = ""
				local_targetrole = self.state.get_singlecolumn_field_list(
					"KillsTargetRole"
				)
				local_bodypart = self.state.get_singlecolumn_field_list(
					"KillsBodyPart"
				)
				pre_local_incmod = self.state.get_singlecolumn_field_list(
					"KillsModInc"
				)
				local_incmod = [[item] for item in pre_local_incmod]
				pre_local_excmod = self.state.get_singlecolumn_field_list(
					"KillsModExc"
				)
				local_excmod = [[item] for item in pre_local_excmod]
				local_dist = val_field(self.ui.fld_dist_cck.displayText(), "", 0, int)
				local_timefrom = val_field(
					self.ui.fld_time_from_cck.displayText(), "", 0, int
				)
				local_timeto = val_field(
					self.ui.fld_time_to_cck.displayText(), "", 0, int
				)

				cond = {
					"bodyPart": local_bodypart,
					"compareMethod": ">=",  # hard code for kill quest
					"conditionType": "Kills",
					"daytime": {"from": local_timefrom, "to": local_timeto},
					"distance": {
						"compareMethod": self.ui.box_dist_compare_cck.currentText(),
						"distance": local_dist,
					},
					"dynamicLocale": False,
					"enemyEquipmentExclusive": [],
					"enemyEquipmentInclusive": [],
					"enemyHealthEffects": [],
					"id": subtask_id,
					"resetOnSessionEnd": self.ui.chk_cck_reset_sessionend.isChecked(),
					"savageRole": local_targetrole,
					"target": local_targets,
					"value": 1,
					"weapon": local_weapons_id,
					"weaponCaliber": [],
					"weaponModsExclusive": local_excmod,
					"weaponModsInclusive": local_incmod,
				}
			case "ExitStatus":
				local_status = self.state.get_singlecolumn_field_list(
					"ExitStatus"
				)
				cond = {
					"conditionType": "ExitStatus",
					"dynamicLocale": False,
					"id": subtask_id,
					"status": local_status,
				}
			case "ExitName":
				cond = {
					"conditionType": "ExitName",
					"dynamicLocale": False,
					"id": subtask_id,
					"exitName": self.ui.fld_exitname_ccen.displayText(),
				}
			case "Location":
				local_locations = self.state.get_singlecolumn_field_list(
					"Location"
				)
				cond = {
					"conditionType": "Location",
					"dynamicLocale": False,
					"id": subtask_id,
					"target": local_locations,
				}
			case "Equipment":
				# This is all kind of a lot of work, but basically it's grouping the lists by org(or_group) for a list of multiple lists.
				# So, you can have (this set of 3 equip items) OR  (this other set of 2), etc.
				local_eqi = self.state.get_multicolumn_values_list(
					"EquipmentInclusive"
				)
				local_eqe = self.state.get_multicolumn_values_list(
					"EquipmentExclusive"
				)
				local_eqi_dict = {}
				local_eqe_dict = {}
				for e in local_eqi:
					if e["org"] not in local_eqi_dict:
						local_eqi_dict[e["org"]] = [e["id"]]
					else:
						local_eqi_dict[e["org"]].append(e["id"])

				for e in local_eqe:
					if e["org"] not in local_eqe_dict:
						local_eqe_dict[e["org"]] = [e["id"]]
					else:
						local_eqe_dict[e["org"]].append(e["id"])

				cond = {
					"IncludeNotEquippedItems": self.ui.cb_eq_uneq.isChecked(),
					"conditionType": "Equipment",
					"dynamicLocale": False,
					"equipmentExclusive": list(local_eqe_dict.values()),
					"equipmentInclusive": list(local_eqi_dict.values()),
					"id": subtask_id,
				}
			case "Shots":
				local_bodypart = self.state.get_singlecolumn_field_list(
					"ShotsBodyPart"
				)
				local_targetrole = self.state.get_singlecolumn_field_list(
					"ShotsTargetRole"
				)
				local_weapons = self.state.get_singlecolumn_field_list(
					"ShotsWeapon"
				)
				local_modinc = self.state.get_singlecolumn_field_list(
					"ShotsModsInclusive"
				)
				local_modexc = self.state.get_singlecolumn_field_list(
					"ShotsModsExclusive"
				)
				local_dist = val_field(self.ui.fld_dist_sh.displayText(), "", 0, int)
				local_timefrom = val_field(
					self.ui.fld_timefrom_sh.displayText(), "", 0, int
				)
				local_timeto = val_field(
					self.ui.fld_timeto_sh.displayText(), "", 0, int
				)
				local_value = val_field(self.ui.fld_value_sh.displayText(), "", 0, int)
				cond = {
					"bodyPart": local_bodypart,
					"compareMethod": ">=",
					"conditionType": "Shots",
					"daytime": {"from": local_timefrom, "to": local_timeto},
					"distance": {
						"compareMethod": self.ui.box_distcomp_sh.currentText(),
						"value": local_dist,
					},
					"dynamicLocale": False,
					"enemyEquipmentExclusive": [],
					"enemyEquipmentInclusive": [],
					"enemyHealthEffects": [],
					"id": subtask_id,
					"resetOnSessionEnd": self.ui.chk_cck_reset_sessionend_2.isChecked(),
					"savageRole": local_targetrole,
					"target": self.ui.box_target_sh.currentText(),
					"value": local_value,
					"weapon": [],
					"weaponCaliber": [],
					"weaponModsExclusive": local_modexc,
					"weaponModsInclusive": local_modinc,
				}
			case "HealthEffect":
				local_enval = val_field(self.ui.fld_enval_he.displayText(), "", 0, int)
				local_timeval = val_field(
					self.ui.fld_timeval_he.displayText(), "", 0, int
				)
				local_hydval = val_field(
					self.ui.fld_hydval_he.displayText(), "", 0, int
				)
				local_bodypart = self.state.get_singlecolumn_field_list(
					"HealthEffectBodyPart"
				)
				local_effect = self.state.get_singlecolumn_field_list(
					"HealthEffectEffects"
				)
				cond = {
					"bodyPartsWithEffects": [
						{"bodyParts": local_bodypart, "effects": local_effect}
					],
					"conditionType": "HealthEffect",
					"dynamicLocale": False,
					"energy": {
						"compareMethod": self.ui.box_encomp_he.currentText(),
						"value": local_enval,
					},
					"hydration": {
						"compareMethod": self.ui.box_hydcomp_he.currentText(),
						"value": local_hydval,
					},
					"id": subtask_id,
					"time": {
						"compareMethod": self.ui.box_timecomp_he.currentText(),
						"value": local_timeval,
					},
				}
			case "HealthBuff":
				local_buff = self.state.get_singlecolumn_field_list(
					"HealthBuff"
				)
				cond = {
					"conditionType": "HealthBuff",
					"dynamicLocale": False,
					"id": subtask_id,
					"target": local_buff,
				}
			case "LaunchFlare":
				cond = {
					"conditionType": "LaunchFlare",
					"dynamicLocale": False,
					"id": subtask_id,
					"target": self.ui.fld_fl_zone.displayText(),
				}
			case "InZone":
				local_zone = self.state.get_singlecolumn_field_list("InZone")
				cond = {
					"conditionType": "InZone",
					"dynamicLocale": False,
					"id": subtask_id,
					"zoneIds": local_zone,
				}

		add_table_field(
			self.state,
			f"CounterCreator",
			self.ui.tb_cc,
			subtask_id,
			{0: subtask_id, 1: cond_type},
			cond,
		)

	def finalize(self, cond_type):
		timing = ""
		match cond_type:
			# 3 different types of ids, all unique:
			# one, each cc list item has its own id
			# two, the whole cc list itself has an id
			# three, the top-level CC task/condition has an id
			# we use number 3 for the id in the internal datastore, and show that id in the task/cond list
			case "CounterCreator":
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				local_counter = {"conditions": [], "id": new_id()}
				local_counter["conditions"] = (
					self.state.get_multicolumn_values_list("CounterCreator")
				)
				local_value = val_field(
					self.ui.fld_quantity_cc.displayText(), "", 0, int
				)
				timing = self.ui.box_ff.currentText()
				cond = {
					"completeInSeconds": 0,
					"conditionType": "CounterCreator",
					"counter": local_counter,
					"doNotResetIfCounterCompleted": False,  # TODO: implement gui for this
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"isNecessary": False,  # TODO: implement gui for this
					"isResetOnConditionFailed": False,  # TODO: implement gui for this
					"oneSessionOnly": False,
					"parentId": self.ui.fld_parentid_cc.displayText(),
					"type": self.ui.box_cc_qtlab.currentText(),
					"value": local_value,
					"visibilityConditions": local_vis_cond,
				}
			case "Item":
				sub_cond_type = self.ui.box_hofind_it.currentText()
				if sub_cond_type == "FindItem":
					local_vis_cond = self.state.get_singlecolumn_field_list(
						"VisibilityCond"
					)
					timing = self.ui.box_ff_it.currentText()
					local_target = self.state.get_singlecolumn_field_list(
						"HFItems"
					)
					local_value = val_field(
						self.ui.fld_quantity_it.displayText(), "", 0, int
					)

					cond = {
						"conditionType": "FindItem",
						"countInRaid": False,
						"dogtagLevel": 0,
						"dynamicLocale": False,
						"globalQuestCounterId": "",
						"id": self.id,
						"index": 0,
						"inEncoded": False,
						"maxDurability": val_field(
							self.ui.fld_maxdur_it.displayText(), "", 100, int
						),
						"minDurability": val_field(
							self.ui.fld_mindur_it.displayText(), "", 0, int
						),
						"onlyFoundInRaid": is_true(
							self.ui.box_only_fir_it.currentText()
						),
						"parentId": self.ui.fld_parentid_it.displayText(),
						"target": local_target,
						"value": local_value,
						"visibilityConditions": local_vis_cond,
					}

				if sub_cond_type == "HandoverItem":
					local_vis_cond = self.state.get_singlecolumn_field_list(
						"VisibilityCond"
					)
					timing = self.ui.box_ff_it.currentText()
					local_target = self.state.get_singlecolumn_field_list(
						"HFItems"
					)
					local_value = val_field(
						self.ui.fld_quantity_it.displayText(), "", 0, int
					)
					cond = {
						"conditionType": "HandoverItem",
						"dogtagLevel": 0,
						"dynamicLocale": False,
						"globalQuestCounterId": "",
						"id": self.id,
						"index": 0,
						"inEncoded": False,
						"minDurability": val_field(
							self.ui.fld_mindur_it.displayText(), "", 0, int
						),
						"maxDurability": val_field(
							self.ui.fld_maxdur_it.displayText(), "", 100, int
						),
						"onlyFoundInRaid": is_true(
							self.ui.box_only_fir_it.currentText()
						),
						"parentId": self.ui.fld_parentid_it.displayText(),
						"target": local_target,
						"value": local_value,
						"visibilityConditions": local_vis_cond,
					}

			case "Skill":
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				timing = self.ui.box_ff_sk.currentText()
				local_value = val_field(self.ui.fld_level_sk.displayText(), "", 0, int)
				cond = {
					"compareMethod": self.ui.box_compare_sk.currentText(),
					"conditionType": "Skill",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": self.ui.fld_parentid_sk_2.displayText(),
					"target": self.ui.box_target_sk.currentText(),
					"value": local_value,
					"visibilityConditions": local_vis_cond,
				}
			case "LeaveItemAtLocation":
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				local_target_ids = self.state.get_singlecolumn_field_list(
					"LeaveItemTarget"
				)
				timing = self.ui.box_ff_li.currentText()
				local_ptime = val_field(
					self.ui.fld_plant_time_li.displayText(), "", 0, int
				)
				local_value = val_field(
					self.ui.fld_quantity_li.displayText(), "", 0, int
				)
				cond = {
					"conditionType": "LeaveItemAtLocation",
					"dogtagLevel": 0,
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"inEncoded": False,
					"minDurability": val_field(
						self.ui.fld_mindur_li.displayText(), "", 0, int
					),
					"maxDurability": val_field(
						self.ui.fld_mindur_li.displayText(), "", 100, int
					),
					"onlyFoundInRaid": is_true(self.ui.box_fir_li.currentText()),
					"parentId": self.ui.fld_parentid_li.displayText(),
					"plantTime": local_ptime,
					"target": local_target_ids,
					"value": local_value,
					"visibilityConditions": local_vis_cond,
					"zoneId": self.ui.fld_zoneid_li.displayText(),
				}
			case "PlaceBeacon":
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				timing = self.ui.box_ff_pb.currentText()
				local_ptime = val_field(self.ui.sb_time_pb.cleanText(), "", 10, int)
				local_value = val_field(self.ui.sb_value_pb.cleanText(), "", 1, int)
				cond = {
					"conditionType": "PlaceBeacon",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": self.ui.fld_parentid_pb.displayText(),
					"plantTime": local_ptime,
					"target": [
						"5991b51486f77447b112d44f"
					],  # ItemID for the MS2000 marker, can also use Radio Repeater (63a0b2eabea67a6d93009e52) according to docs
					"value": local_value,
					"visibilityConditions": local_vis_cond,
					"zoneId": self.ui.fld_zoneid_pb.displayText(),
				}
			case "WeaponAssembly":
				# TODO: implement
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				timing = "Finish"
				cond = {
					"weapon_assembly_placeholder": "add_weapon_assembly_object_here"
				}
				pass
			case "TraderLoyalty":
				local_vis_cond = self.state.get_singlecolumn_field_list(
					"VisibilityCond"
				)
				timing = self.ui.box_ff_tl.currentText()
				local_value = val_field(self.ui.fld_level_tl.displayText(), "", 0, int)
				cond = {
					"compareMethod": self.ui.box_compare_tl.currentText(),
					"conditionType": "TraderLoyalty",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": self.ui.fld_parentid_tl.displayText(),  # TODO: this isn't actually in the docs, does it work?? remove if not
					"target": self.state.traders[
						self.ui.box_target_tl.currentText()
					],
					"value": local_value,
					"visibilityConditions": local_vis_cond,
				}

			# These 3 next are start-only
			case "Level":
				timing = "Start"
				local_value = val_field(self.ui.fld_value_lv.displayText(), "", 0, int)
				cond = {
					"compareMethod": self.ui.box_compare_lv.currentText(),
					"conditionType": "Level",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": "",
					"value": local_value,
					"visibilityConditions": [],
				}
			case "Quest":
				timing = self.ui.box_timing_qs.currentText()
				local_status = self.state.get_singlecolumn_field_list("QStatus")
				local_status_int = [self.state.status[s] for s in local_status]
				local_availafter = val_field(
					self.ui.fld_avail_qs.displayText(), "", 0, int
				)
				cond = {
					"availableAfter": local_availafter,
					"conditionType": "Quest",
					"dispersion": 0,
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": "",
					"status": local_status_int,
					"target": self.ui.fld_tid_qs.displayText(),
					"visibilityConditions": [],
				}
			case "TraderStanding":
				timing = "Start"
				local_availafter = val_field(
					self.ui.fld_value_ts.displayText(), "", 0, int
				)
				cond = {
					"compareMethod": self.ui.box_comparemethod_ts.currentText(),
					"conditionType": "TraderStanding",
					"dynamicLocale": False,
					"globalQuestCounterId": "",
					"id": self.id,
					"index": 0,
					"parentId": "",
					"target": self.state.traders[
						self.ui.box_trader_ts.currentText()
					],
					"value": local_value,
					"visibilityConditions": [],
				}

		self.condition_ready.emit(timing, cond_type, self.id, cond)
		self.close()

	# def load_settings_from_dict(self, settings, condition_timing):
	#       print(f"Loading condition from dict: {settings}")
	#       self.id = settings["id"]
	#       self.ui.fld_taskid_gen.setText(settings["id"]) # update the Cond ID field to match the import
	#       # first field is the JSON key
	#       # tuple is (item reference to set, type of item reference (determines func to set))
	#       condition_type = settings["conditionType"]
	#       # todo - more robust for rewards missing fields; need to build a better validator
	#       # doing just the unknown for now since it is missing in Legs' test json
	#       print(f"Cond type: {condition_type}, timing: {condition_timing}")

	#       for viscon in settings["visibilityConditions"]:
	#         self.state.add_table_field(f"VisibilityCond", self.ui.tb_vis, viscon, {0: viscon}, viscon)

	#       match condition_type:
	#         case "CounterCreator":
	#           # Editing a CC condition doesn't really do much as implemented because there is no edit CC subtask yet
	#           # TODO: Add edit subtask for CC
	#           self.ui.tabWidget.setCurrentIndex(0)
	#           for cc_item in settings["counter"]["conditions"]:
	#             self.state.add_table_field(f"CounterCreator", self.ui.tb_cc, cc_item["id"], {0: cc_item["id"], 1: cc_item["conditionType"]}, cc_item)
	#         case "FindItem" | "HandoverItem":
	#           self.ui.tabWidget.setCurrentIndex(1)
	#           self.ui.box_hofind_it.setCurrentText(condition_type)
	#           self.ui.box_only_fir_it.setCurrentText(str(settings["onlyFoundInRaid"]).lower())
	#           self.ui.box_ff_it.setCurrentText(condition_timing)
	#           self.ui.fld_dogtaglev_it.setText(str(settings["dogtagLevel"]))
	#           self.ui.fld_parentid_it.setText(settings["parentId"])
	#           self.ui.fld_maxdur_it.setText(str(settings["maxDurability"]))
	#           self.ui.fld_mindur_it.setText(str(settings["minDurability"]))
	#           self.ui.fld_quantity_it.setText(str(settings["value"]))
	#           for itemid in settings["target"]:
	#             self.state.add_table_field(f"HFItems", self.ui.tb_items, itemid, {0: itemid}, itemid)
	#         case "Skill":
	#           self.ui.tabWidget.setCurrentIndex(2)
	#           self.ui.box_compare_sk.setCurrentText(settings["compareMethod"])
	#           self.ui.box_target_sk.setCurrentText(settings["target"])
	#           self.ui.box_ff_sk.setCurrentText(condition_timing)
	#           self.ui.fld_level_sk.setText(str(settings["value"]))
	#           self.ui.fld_parentid_sk_2.setText(settings["parentId"])
	#         case "LeaveItemAtLocation":
	#           self.ui.tabWidget.setCurrentIndex(3)
	#           self.ui.box_fir_li.setCurrentText(str(settings["onlyFoundInRaid"]).lower())
	#           self.ui.box_ff_li.setCurrentText(condition_timing)
	#           self.ui.fld_zoneid_li.setText(settings["zoneId"])
	#           self.ui.fld_dogtaglevel_li.setText(str(settings["dogtagLevel"]))
	#           self.ui.fld_mindur_li.setText(str(settings["minDurability"]))
	#           self.ui.fld_maxdur_li.setText(str(settings["maxDurability"]))
	#           self.ui.fld_plant_time_li.setText(str(settings["plantTime"]))
	#           self.ui.fld_quantity_li.setText(str(settings["value"]))
	#           self.ui.fld_parentid_li.setText(settings["parentId"])
	#           for tid in settings["target"]:
	#             self.state.add_table_field(f"LeaveItemTarget", self.ui.tb_li_target, tid, {0: tid}, tid)
	#         case "WeaponAssembly":
	#           self.ui.tabWidget.setCurrentIndex(5)
	#           # TODO: Implement WeaponAssembly
	#         case "PlaceBeacon":
	#           self.ui.tabWidget.setCurrentIndex(4)
	#           self.ui.sb_time_pb.setValue(int(settings["plantTime"]))
	#           self.ui.sb_value_pb.setValue(int(settings["value"]))
	#           self.ui.fld_zoneid_pb.setText(settings["zoneId"])
	#           self.ui.fld_parentid_pb.setText(settings["parentId"])
	#           self.ui.box_ff_pb.setCurrentText(settings[condition_timing])
	#         case "TraderLoyalty":
	#           target_str = self.state.traders_invert[settings["target"]]
	#           self.ui.tabWidget.setCurrentIndex(6)
	#           self.ui.box_compare_tl.setCurrentText(settings["compareMethod"])
	#           self.ui.box_target_tl.setCurrentText(target_str)
	#           self.ui.box_ff_tl.setCurrentText(condition_timing)
	#           self.ui.fld_level_tl.setText(str(settings["value"]))
	#           self.ui.fld_parentid_tl.setText(settings["parentId"])
	#         case "Level":
	#           self.ui.tabWidget_2.setCurrentIndex(1)
	#           self.ui.tabWidget_3.setCurrentIndex(0)
	#           self.ui.box_compare_lv.setCurrentText(settings["compareMethod"])
	#           self.ui.fld_value_lv.setText(str(settings["value"]))
	#         case "Quest":
	#           self.ui.tabWidget_2.setCurrentIndex(1)
	#           self.ui.tabWidget_3.setCurrentIndex(1)
	#           self.ui.fld_avail_qs.setText(str(settings["availableAfter"]))
	#           self.ui.fld_tid_qs.setText(str(settings["target"]))
	#           for status in settings["status"]:
	#             str_status = self.state.status_invert[status]
	#             self.state.add_table_field(f"QStatus", self.ui.tb_status_qs, str_status, {0: str_status}, str_status)
	#         case "TraderStanding":
	#           trader = self.state.traders_invert[settings["target"]]
	#           self.ui.tabWidget_2.setCurrentIndex(1)
	#           self.ui.tabWidget_3.setCurrentIndex(2)
	#           self.ui.box_comparemethod_ts.setCurrentText(settings["compareMethod"])
	#           self.ui.box_trader_ts.setCurrentText(trader)
	#           self.ui.fld_value_ts.setText(settings["value"])
