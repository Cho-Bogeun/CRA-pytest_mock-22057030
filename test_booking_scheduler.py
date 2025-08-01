from datetime import datetime, timedelta

import pytest

from schedule import Customer, Schedule
from communication import SmsSender, MailSender
from booking_scheduler import BookingScheduler
from test_communication import TestableSmsSender, TestableMailSender

NOT_ON_THE_HOUR = datetime.strptime("2025/08/01 09:05", "%Y/%m/%d %H:%M")
ON_THE_HOUR = datetime.strptime("2025/08/01 09:00", "%Y/%m/%d %H:%M")
CUSTOMER = Customer("Fake name", "010-1234-5678")
CUSTOMER_WITH_EMAIL = Customer("Fake name", "010-1234-5678", "test@example.com")

CAPACITY_PER_HOUR = 3
UNDER_CAPACITY = 1

@pytest.fixture
def boocking_scheduler():
    return BookingScheduler(CAPACITY_PER_HOUR)

def test_예약은_정시에만_가능하다_정시가_아닌경우_예약불가(boocking_scheduler):
    schedule = Schedule(NOT_ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)

    with pytest.raises(ValueError):
        boocking_scheduler.add_schedule(schedule)

def test_예약은_정시에만_가능하다_정시인_경우_예약가능(boocking_scheduler):
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)

    boocking_scheduler.add_schedule(schedule)

    assert boocking_scheduler.has_schedule(schedule)

def test_시간대별_인원제한이_있다_같은_시간대에_Capacity_초과할_경우_예외발생(boocking_scheduler):
    schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
    boocking_scheduler.add_schedule(schedule)

    with pytest.raises(ValueError, match="Number of people is over restaurant capacity per hour"):
        new_schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY,CUSTOMER)
        boocking_scheduler.add_schedule(new_schedule)

def test_시간대별_인원제한이_있다_같은_시간대가_다르면_Capacity_차있어도_스케쥴_추가_성공(boocking_scheduler):
    schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, CUSTOMER)
    boocking_scheduler.add_schedule(schedule)

    different_hour = ON_THE_HOUR + timedelta(hours=1)
    new_schedule = Schedule(different_hour, UNDER_CAPACITY, CUSTOMER)
    boocking_scheduler.add_schedule(new_schedule)

    assert  boocking_scheduler.has_schedule(schedule)
    assert  boocking_scheduler.has_schedule(new_schedule)

@pytest.fixture
def boocking_scheduler_with_sms_mock(boocking_scheduler):
    testable_sms_sender = TestableSmsSender()
    boocking_scheduler.set_sms_sender(testable_sms_sender)

    return boocking_scheduler, testable_sms_sender

def test_예약완료시_SMS는_무조건_발송(boocking_scheduler_with_sms_mock):
    boocking_scheduler, testable_sms_sender = boocking_scheduler_with_sms_mock
    boocking_scheduler.set_sms_sender(testable_sms_sender)
    schedule = Schedule(ON_THE_HOUR,UNDER_CAPACITY,CUSTOMER)

    boocking_scheduler.add_schedule(schedule)

    assert testable_sms_sender.send_called

@pytest.fixture
def boocking_scheduler_with_mail_mock(boocking_scheduler):
    testable_mail_sender = TestableMailSender()
    boocking_scheduler.set_mail_sender(testable_mail_sender)

    return boocking_scheduler, testable_mail_sender

def test_이메일이_없는_경우에는_이메일_미발송(boocking_scheduler_with_mail_mock):
    boocking_scheduler, testable_mail_sender = boocking_scheduler_with_mail_mock
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER)

    boocking_scheduler.add_schedule(schedule)

    assert testable_mail_sender.send_mail_count == 0

def test_이메일이_있는_경우에는_이메일_발송(boocking_scheduler_with_mail_mock):
    boocking_scheduler, testable_mail_sender = boocking_scheduler_with_mail_mock
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_EMAIL)

    boocking_scheduler.add_schedule(schedule)

    assert testable_mail_sender.send_mail_count == 1

class TestableBoockingScheduler(BookingScheduler):
    def __init__(self, capacity_per_hour, date_time: str):
        super().__init__(capacity_per_hour)
        self._date_time = date_time

    def get_now(self):
        return datetime.strptime(self._date_time, "%Y/%m/%d %H:%M")

def test_현재날짜가_일요일인_경우_예약불가_예외처리():
    boocking_scheduler = TestableBoockingScheduler(CAPACITY_PER_HOUR, "2025/08/03 09:05")
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_EMAIL)

    with pytest.raises(ValueError):
        boocking_scheduler.add_schedule(schedule)

def test_현재날짜가_일요일이_아닌경우_예약가능():
    boocking_scheduler = TestableBoockingScheduler(CAPACITY_PER_HOUR, "2025/08/04 09:05")
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, CUSTOMER_WITH_EMAIL)

    boocking_scheduler.add_schedule(schedule)

    assert boocking_scheduler.has_schedule(schedule)
