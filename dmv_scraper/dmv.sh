CAPTCHA="03AOLTBLQlSdbUEqkQQNUrGwbnuk8X4z0vVIs1Rbl2uncd-aEQ9SUMapETNKekA7wvGlnCaBDhWBRPZrO4Eia-LcuXQw2gfge3SjJHgOsG4VIVJ8GTkcaC4WmuU6Zpopxi-a5eJwuVw0XMdYqZogsffPSHahzboVZAWNtFpMxt5WwHcVkuUwootmZHRHVOkVEUsadjiZyE8ywTZliwxid-3jAffp1jdEgTIn0UPvWFf666e18Pvw4x9XdSSuni7OYJ2rtX5pdbWQ9Dy7_J0DlQIRdufvuIu7AVmsjf7lWsWQrC2v59bXAEmxXis0Fkqp1J6ZFba6Urh_Bo"

TSHIT="019de3c5d956079e020d475d8793a0f608e810d2aef8e108a88def996c2389e40748e54ce1"

# SEQUENCE:
# START: TS013cb4be=019de3c5d901ce94dda135643fb530742cd636c4abe2381bfc85c075d80472ffe41429aa10
#      : TS013cb4be=019de3c5d901ce94dda135643fb530742cd636c4abe2381bfc85c075d80472ffe41429aa10
#      : TS013cb4be=019de3c5d901ce94dda135643fb530742cd636c4abe2381bfc85c075d80472ffe41429aa10
#      : TS013cb4be=019de3c5d956079e020d475d8793a0f608e810d2aef8e108a88def996c2389e40748e54ce1
#      : TS013cb4be=019de3c5d956079e020d475d8793a0f608e810d2aef8e108a88def996c2389e40748e54ce1
#      : TS013cb4be=019de3c5d956079e020d475d8793a0f608e810d2aef8e108a88def996c2389e40748e54ce1
# TS013cb4be=019de3c5d956079e020d475d8793a0f608e810d2aef8e108a88def996c2389e40748e54ce1
#

# OFFICE_IDS="537 587 661 570 529 679 641 582 576 606 585 528 597 550 625 520 613 580 603 564 581 523 534 628 524 514 599 598 615 669 527 556 685 526 621 643 655 657 590 644 505 646 607 627 498 623 510 670 693 541 565 609 579 635 546 508 652 578 610 521 647 605 687 530 595 617 622 692 507 502 650 640 533 658 566 536 557 511 639 540 584 662 586 686 504 604 596 522 636 683 659 601 509 574 634 592 525 631 532 573 676 544 612 558 551 626 548 633 577 545 656 673 543 501 602 539 568 512 648 506 519 503 516 645 547 689 593 619 677 542 549 632 563 616 630 555 668 567 660 680 569 538 698 517 531 575 672 663 608 642 513 594 553 649 638 535 588 554 515 560 629 559 624 583 572 618 611 591 571 637 561 552 562"
OFFICE_IDS="596 587"

echo "Init Cookies from cookie-jar.init"
cp cookie-jar.init cookie-jar-result.out

for officeId in $OFFICE_IDS; do
  COOKIE="PD_STATEFUL_053e91ee-3463-11e4-bb11-a224edf30402=%2Fportal; DMV.CA.GOV=2779298438.47873.0000; PD_STATEFUL_00bcef52-0c5a-11e4-98a1-a224e2a50102=%2Fwasapp; AMWEBJCT!%2Fwasapp!JSESSIONID=0000jbq3YhK11GHFx06Z92CE9db:18u4c282j; TS013cb4be=$TSHIT"

  OUT="results/$officeId.html"
  echo "Running $officeId"
	curl -X POST -L -s "https://www.dmv.ca.gov/wasapp/foa/findDriveTest.do" \
		-H "Cookie: $COOKIE" \
		-c "cookie-jar-result.out" \
		-F "numberItems=1" \
		-F "mode=DriveTest" \
		-F "officeId=$officeId" \
		-F "requestedTask=DT" \
		-F "firstName=KATARINA" \
		-F "lastName=SABOVA" \
		-F "dlNumber=Y7788070" \
		-F "birthYear=1989" \
		-F "birthMonth=05" \
		-F "birthDay=30" \
		-F "telArea=415" \
		-F "telPrefix=202" \
		-F "telSuffix=3034" \
		-F "resetCheckFields=true" \
		-o $OUT

  TSHIT=`grep TS013 cookie-jar-result.out | cut -f7`
  echo "TSHIT=$TSHIT"
	#-F "g-recaptcha-response=$CAPTCHA" \
	#-F "captchaResponse=$CAPTCHA" \

  ls -l $OUT
	less $OUT | grep -A 10 'data-title="Office"' | grep -A 1 '<p' | tail -1 | awk '{print $1, $2}'
	less $OUT | grep -A 10 'data-title="Appointment"' | grep -A 3 strong | tail -3 | awk '{print $1,$2,$3}' | head -1

  COOKIE="PD_STATEFUL_053e91ee-3463-11e4-bb11-a224edf30402=%2Fportal; DMV.CA.GOV=2779298438.47873.0000; PD_STATEFUL_00bcef52-0c5a-11e4-98a1-a224e2a50102=%2Fwasapp; AMWEBJCT!%2Fwasapp!JSESSIONID=0000jbq3YhK11GHFx06Z92CE9db:18u4c282j; TS013cb4be=$TSHIT"

  echo "Go to start"
  curl -L -s "https://www.dmv.ca.gov/wasapp/foa/startDriveTest.do" \
		-H "Cookie: $COOKIE" \
		-c "cookie-jar-start.out" \
		-o start.html
  TSHIT=`grep TS013 cookie-jar-start.out | cut -f7`
  echo "TSHIT=$TSHIT"

done


# dl_number
