frappe.ui.form.on("Notification", {
	refresh(frm) {
		_apply_message_type(frm);

		if (frm.doc.letter) {
			frm.add_custom_button(__("Open Letter"), () => {
				window.open(`/app/letter-builder/${frm.doc.letter}?tab=notifications`, "_blank");
			}, __("Letters"));
		} else {
			frm.add_custom_button(__("Design with Letters"), async () => {
				if (frm.is_new()) {
					frappe.msgprint(__("Please save the notification first, then use Design with Letters."));
					return;
				}
				frm.disable_save();
				try {
					const res = await frappe.call({
						method: "letters.letters.api.notifications.create_letter_for_notification",
						args: { notification: frm.doc.name },
					});
					const letterName = res.message.letter;
					frm.set_value("letter", letterName);
					frm.set_value("letter_message_type", "Letter Builder");
					await frm.save();
					window.open(`/app/letter-builder/${letterName}?tab=notifications`, "_blank");
				} finally {
					frm.enable_save();
				}
			}, __("Letters"));
		}
	},

	letter_message_type(frm) {
		_apply_message_type(frm);
	},
});

function _apply_message_type(frm) {
	const isLetterBuilder = frm.doc.letter_message_type === "Letter Builder";
	frm.set_df_property("message", "read_only", isLetterBuilder ? 1 : 0);
	frm.set_df_property("letter", "read_only", isLetterBuilder ? 0 : 1);
	frm.refresh_field("message");
	frm.refresh_field("letter");
}
