from azulbrief.models import Source
from azulbrief.segmenter import segment_sources
def test_ids_are_stable_and_content_derived():
    s=Source(url="https://example.com/engineering",title="Engineering",source_type="engineering",text="We operate critical Java services in production.")
    assert segment_sources([s])[0].id==segment_sources([s])[0].id
    changed=s.model_copy(update={"text":"We operate critical Go services in production."})
    assert segment_sources([s])[0].id!=segment_sources([changed])[0].id

