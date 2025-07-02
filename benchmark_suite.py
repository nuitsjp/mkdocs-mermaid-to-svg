from project_name.utils.helpers import chunk_list


def test_chunk_list_benchmark(benchmark):
    data = list(range(1000))
    result = benchmark(chunk_list, data, 10)
    assert len(result) == 100
