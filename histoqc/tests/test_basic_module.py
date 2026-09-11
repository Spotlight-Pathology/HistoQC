import openslide
from histoqc.BasicModule import getBasicStats


class FakeOsHandle:
    """Stands in for openslide.OpenSlide when only .properties is needed."""

    def __init__(self, properties):
        self.properties = properties


class FakeState(dict):
    """Minimal stand-in for BaseImage - just enough for getBasicStats."""

    def addToPrintList(self, name, val):
        self[name] = val


def test_get_basic_stats_reads_dicom_scanner_metadata():
    s = FakeState(filename='fake.dcm')
    s['os_handle'] = FakeOsHandle({
        'openslide.vendor': 'dicom',
        'dicom.Manufacturer': '3DHISTECH Kft.',
        'dicom.ManufacturerModelName': 'Pannoramic 1000',
    })

    getBasicStats(s, {})

    assert s['scanner_manufacturer'] == '3DHISTECH Kft.'
    assert s['scanner_model'] == 'Pannoramic 1000'


def test_get_basic_stats_scanner_metadata_na_for_non_dicom(svs_small):
    # Aperio (and every other non-DICOM OpenSlide backend) has no equivalent
    # to dicom.Manufacturer/dicom.ManufacturerModelName, so these fields must
    # fall back to "NA" - the same default used for every other field in
    # getBasicStats - rather than None or raising.
    s = FakeState(filename='fake.svs')
    s['os_handle'] = openslide.OpenSlide(str(svs_small))

    getBasicStats(s, {})

    assert s['type'] == 'aperio'
    assert s['scanner_manufacturer'] == 'NA'
    assert s['scanner_model'] == 'NA'
