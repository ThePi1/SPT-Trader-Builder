"""New ids are laid out like Mongo ObjectIds (core/ids.py)."""

import threading
import time

from core import ids


def test_a_new_id_is_24_hex_characters_that_is_id_accepts():
	for _ in range(50):
		value = ids.new_id()
		assert len(value) == 24 and value == value.lower() and ids.is_id(value)


def test_the_first_four_bytes_are_the_time():
	before = int(time.time())
	value = ids.new_id()
	after = int(time.time())
	assert before <= int(value[:8], 16) <= after


def test_the_middle_five_bytes_stay_the_same_for_a_run_and_the_counter_goes_up_by_one():
	first, second, third = ids.new_id(), ids.new_id(), ids.new_id()
	assert first[8:18] == second[8:18] == third[8:18]
	counts = [int(v[18:], 16) for v in (first, second, third)]
	assert [(b - a) % 0x1000000 for a, b in zip(counts, counts[1:])] == [1, 1]


def test_many_ids_in_a_row_are_all_different_even_in_the_same_second():
	made = [ids.new_id() for _ in range(100_000)]
	assert len(set(made)) == len(made)


def test_ids_made_in_several_threads_do_not_clash():
	made, lock = [], threading.Lock()

	def work():
		mine = [ids.new_id() for _ in range(5000)]
		with lock:
			made.extend(mine)

	threads = [threading.Thread(target=work) for _ in range(8)]
	for thread in threads:
		thread.start()
	for thread in threads:
		thread.join()
	assert len(made) == 40000 and len(set(made)) == 40000


def test_a_new_process_gets_new_random_bytes(monkeypatch):
	before = ids.new_id()[8:18]
	monkeypatch.setattr(ids.os, "getpid", lambda: ids._process["pid"] + 1)
	after = ids.new_id()[8:18]
	assert before != after  # (the process id changed, so the five random bytes were chosen again)


def test_is_id_checks_the_shape():
	assert ids.is_id("a" * 24) and ids.is_id("A1" * 12)
	assert not ids.is_id("a" * 23) and not ids.is_id("g" * 24) and not ids.is_id(None) and not ids.is_id(5)


def test_ids_are_valid_objectids_for_pymongo_when_it_is_installed():
	import datetime

	import pytest

	bson = pytest.importorskip("bson")  # (only a cross-check: the program itself does not need it)
	for _ in range(20):
		value = ids.new_id()
		assert bson.ObjectId.is_valid(value)
		made = bson.ObjectId(value).generation_time
		assert abs((datetime.datetime.now(datetime.timezone.utc) - made).total_seconds()) < 5
