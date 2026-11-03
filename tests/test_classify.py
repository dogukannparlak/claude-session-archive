import unittest

from session_archive.classify import classify


class ClassifyTests(unittest.TestCase):
    def kind(self, text, **record):
        return classify(record, text)[0]

    def test_plain_human_text(self):
        self.assertEqual(classify({"origin": {"kind": "human"}}, "merhaba"), ("human", "", "merhaba"))

    def test_reminders_and_ide_tags_are_stripped_from_human_text(self):
        text = "<system-reminder>x</system-reminder><ide_opened_file>f</ide_opened_file>\nactual question"
        self.assertEqual(classify({}, text), ("human", "", "actual question"))

    def test_only_harness_context_becomes_meta(self):
        self.assertEqual(classify({}, "<system-reminder>only noise</system-reminder>")[:2], ("meta", "system_context"))

    def test_meta_flag_is_skill_context_or_image(self):
        self.assertEqual(classify({"isMeta": True}, "skill body")[:2], ("meta", "skill_context"))
        self.assertEqual(classify({"isMeta": True}, "[Image: x]")[:2], ("meta", "image_info"))

    def test_origin_kinds(self):
        self.assertEqual(classify({"origin": {"kind": "task-notification"}}, "<task-notification/>")[:2], ("system", "task_notification"))
        self.assertEqual(classify({"origin": {"kind": "peer"}}, "x")[:2], ("system", "peer_message"))
        self.assertEqual(classify({"origin": {"kind": "auto-continuation"}}, "x")[:2], ("system", "auto_continue"))

    def test_interrupt_summary_shell_and_command(self):
        self.assertEqual(self.kind("[Request interrupted by user]"), "interrupt")
        self.assertEqual(classify({}, "This session is being continued from a previous...")[:2], ("system", "session_summary"))
        self.assertEqual(classify({}, "<bash-input>ls -la</bash-input>"), ("shell", "", "ls -la"))
        self.assertEqual(self.kind("<bash-stdout>out</bash-stdout>"), "meta")
        self.assertEqual(
            classify({}, "<command-message>x</command-message> <command-name>/review</command-name> <command-args>--fast</command-args>"),
            ("command", "", "/review --fast"),
        )


if __name__ == "__main__":
    unittest.main()
