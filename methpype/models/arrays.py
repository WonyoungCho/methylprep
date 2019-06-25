# Lib
from enum import Enum, unique


@unique
class ArrayType(Enum):
    CUSTOM = 'custom'
    ILLUMINA_450K = '450k'
    ILLUMINA_EPIC = 'epic'
    ILLUMINA_EPIC_PLUS = 'epic+'

    def __str__(self):
        return self.value

    @classmethod
    def from_probe_count(cls, probe_count):
        """Determines array type using number of probes. Returns array string."""
        if probe_count == 1055583:
            return cls.ILLUMINA_EPIC_PLUS

        if 622000 <= probe_count <= 623000:
            return cls.ILLUMINA_450K

        if 1050000 <= probe_count <= 1053000:
            return cls.ILLUMINA_EPIC

        if 54000 <= probe_count <= 56000:
            raise ValueError('Unsupported array type: Illumina Human Methylation 27k')

        raise ValueError('Unknown array type')

    @property
    def num_probes(self):
        probe_counts = {
            ArrayType.ILLUMINA_450K: 485578,
            ArrayType.ILLUMINA_EPIC: 865919,
            ArrayType.ILLUMINA_EPIC_PLUS: 868699,
        }

        return probe_counts.get(self)

    @property
    def num_controls(self):
        probe_counts = {
            ArrayType.ILLUMINA_450K: 850,
            ArrayType.ILLUMINA_EPIC: 635,
            ArrayType.ILLUMINA_EPIC_PLUS: 635,
        }

        return probe_counts.get(self)


class Array():
    __slots__ = ['name', 'array_type']

    def __init__(self, name, array_type):
        self.name = name
        self.array_type = array_type