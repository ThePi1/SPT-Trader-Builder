"""Problems found in a file, as the validator reports them."""

from dataclasses import dataclass

ERROR = "error"  # SPT can't load the file, or the game breaks
WARNING = "warning"  # loads, but unlike the base game: may be a mistake, or may fail in the game


@dataclass(frozen=True)
class Issue:
	level: str
	path: tuple  # where in the file: keys and list indexes, e.g. ("5936...", "conditions", "Fail", 0, "id")
	message: str  # plain English, shown to the user

	def where(self):
		return ".".join(str(part) for part in self.path)

	def __str__(self):
		return f"{self.level}: {self.where()}: {self.message}"


def errors(issues):
	return [i for i in issues if i.level == ERROR]


def warnings(issues):
	return [i for i in issues if i.level == WARNING]
