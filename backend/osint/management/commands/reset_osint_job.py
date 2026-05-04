"""Reset a stuck OSINT job back to a resumable status."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Reset an OSINT job status to allow resumption (e.g. phase2_processing -> awaiting_terminal_output)"

    def add_arguments(self, parser):
        parser.add_argument("job_id", type=str, help="OsintJob UUID to reset")
        parser.add_argument(
            "--status",
            type=str,
            default="awaiting_terminal_output",
            help="Target status (default: awaiting_terminal_output)",
        )

    def handle(self, *args, **options):
        from osint.models import OsintJob
        job_id = options["job_id"]
        target_status = options["status"]
        try:
            job = OsintJob.objects.get(id=job_id)
            old_status = job.status
            job.status = target_status
            job.save(update_fields=["status"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reset job {job_id} ({job.organization_name}): {old_status} -> {target_status}"
                )
            )
        except OsintJob.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"OsintJob {job_id} not found"))
            raise SystemExit(1)
