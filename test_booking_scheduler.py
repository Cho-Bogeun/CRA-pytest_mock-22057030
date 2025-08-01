from datetime import datetime, timedelta

import pytest
import pytest_mock

from schedule import Customer, Schedule
from communication import SmsSender, MailSender
from booking_scheduler import BookingScheduler

NOT_ON_THE_HOUR = datetime.strptime("2025/08/01 09:05", "%Y/%m/%d %H:%M")
ON_THE_HOUR = datetime.strptime("2025/08/01 09:00", "%Y/%m/%d %H:%M")

CAPACITY_PER_HOUR = 3
UNDER_CAPACITY = 1

@pytest.fixture
def customer(mocker):
    customer = mocker.Mock()
    customer.get_email.return_value = None
    return customer

@pytest.fixture
def customer_with_email(mocker):
    customer = mocker.Mock()
    customer.get_email.return_value = "test@example.com"
    return customer

@pytest.fixture
def boocking_scheduler():
    return BookingScheduler(CAPACITY_PER_HOUR)

def test_예약은_정시에만_가능하다_정시가_아닌경우_예약불가(boocking_scheduler, customer):
    schedule = Schedule(NOT_ON_THE_HOUR, UNDER_CAPACITY, customer)

    with pytest.raises(ValueError):
        boocking_scheduler.add_schedule(schedule)

def test_예약은_정시에만_가능하다_정시인_경우_예약가능(boocking_scheduler, customer):
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer)

    boocking_scheduler.add_schedule(schedule)

    assert boocking_scheduler.has_schedule(schedule)

def test_시간대별_인원제한이_있다_같은_시간대에_Capacity_초과할_경우_예외발생(boocking_scheduler, customer):
    schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, customer)
    boocking_scheduler.add_schedule(schedule)

    with pytest.raises(ValueError, match="Number of people is over restaurant capacity per hour"):
        new_schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer)
        boocking_scheduler.add_schedule(new_schedule)

def test_시간대별_인원제한이_있다_같은_시간대가_다르면_Capacity_차있어도_스케쥴_추가_성공(boocking_scheduler, customer):
    schedule = Schedule(ON_THE_HOUR, CAPACITY_PER_HOUR, customer)
    boocking_scheduler.add_schedule(schedule)

    different_hour = ON_THE_HOUR + timedelta(hours=1)
    new_schedule = Schedule(different_hour, UNDER_CAPACITY, customer)
    boocking_scheduler.add_schedule(new_schedule)

    assert  boocking_scheduler.has_schedule(schedule)
    assert  boocking_scheduler.has_schedule(new_schedule)

@pytest.fixture
def boocking_scheduler_with_sms_mock(boocking_scheduler, mocker):
    testable_sms_sender = mocker.Mock()# TestableSmsSender()
    boocking_scheduler.set_sms_sender(testable_sms_sender)

    return boocking_scheduler, testable_sms_sender

def test_예약완료시_SMS는_무조건_발송(boocking_scheduler_with_sms_mock, customer):
    boocking_scheduler, testable_sms_sender = boocking_scheduler_with_sms_mock
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer)

    boocking_scheduler.add_schedule(schedule)

    testable_sms_sender.send.assert_called()

@pytest.fixture
def boocking_scheduler_with_mail_mock(boocking_scheduler, mocker):
    testable_mail_sender = mocker.Mock()
    boocking_scheduler.set_mail_sender(testable_mail_sender)

    return boocking_scheduler, testable_mail_sender

def test_이메일이_없는_경우에는_이메일_미발송(boocking_scheduler_with_mail_mock, customer):
    boocking_scheduler, testable_mail_sender = boocking_scheduler_with_mail_mock
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer)

    boocking_scheduler.add_schedule(schedule)

    testable_mail_sender.send_mail.assert_not_called()

def test_이메일이_있는_경우에는_이메일_발송(boocking_scheduler_with_mail_mock, customer_with_email):
    boocking_scheduler, testable_mail_sender = boocking_scheduler_with_mail_mock
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer_with_email)

    boocking_scheduler.add_schedule(schedule)

    testable_mail_sender.send_mail.assert_called_once()

class TestableBoockingScheduler(BookingScheduler):
    def __init__(self, capacity_per_hour, date_time: str):
        super().__init__(capacity_per_hour)
        self._date_time = date_time

    def get_now(self):
        return datetime.strptime(self._date_time, "%Y/%m/%d %H:%M")

def test_현재날짜가_일요일인_경우_예약불가_예외처리(customer_with_email):
    boocking_scheduler = TestableBoockingScheduler(CAPACITY_PER_HOUR, "2025/08/03 09:05")
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer_with_email)

    with pytest.raises(ValueError):
        boocking_scheduler.add_schedule(schedule)

def test_현재날짜가_일요일이_아닌경우_예약가능(customer_with_email):
    boocking_scheduler = TestableBoockingScheduler(CAPACITY_PER_HOUR, "2025/08/04 09:05")
    schedule = Schedule(ON_THE_HOUR, UNDER_CAPACITY, customer_with_email)

    boocking_scheduler.add_schedule(schedule)

    assert boocking_scheduler.has_schedule(schedule)
