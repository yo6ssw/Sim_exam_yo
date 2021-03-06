#!/usr/bin/perl

#Prezentul simulator de examen impreuna cu formatul bazelor de intrebari, rezolvarile 
#problemelor, manual de utilizare, instalare, SRS, cod sursa si utilitarele aferente 
#constituie un pachet software gratuit care poate fi distribuit/modificat in termenii 
#licentei libere GNU GPL, asa cum este ea publicata de Free Software Foundation in 
#versiunea 2 sau intr-o versiune ulterioara. Programul, intrebarile si raspunsurile sunt 
#distribuite gratuit, in speranta ca vor fi folositoare, dar fara nicio garantie, 
#sau garantie implicita, vezi textul licentei GNU GPL pentru mai multe detalii.
#Utilizatorul programului, manualelor, codului sursa si utilitarelor are toate drepturile
#descrise in licenta publica GPL.
#In distributia de pe https://github.com/6oskarwN/Sim_exam_yo trebuie sa gasiti o copie a 
#licentei GNU GPL, de asemenea si versiunea in limba romana, iar daca nu, ea poate fi
#descarcata gratuit de pe pagina http://www.fsf.org/
#Textul intrebarilor oficiale publicate de ANCOM face exceptie de la cele de mai sus, 
#nefacand obiectul licentierii GNU GPL, copyrightul fiind al statului roman, dar 
#fiind folosibil in virtutea legii 544/2001 privind liberul acces la informatiile 
#de interes public precum al legii 109/2007 privind reutilizarea informatiilor din
#institutiile publice.

#This program together with question database formatting, solutions to problems, manuals, 
#documentation, sourcecode and utilities is a  free software; you can redistribute it 
#and/or modify it under the terms of the GNU General Public License as published by the 
#Free Software Foundation; either version 2 of the License, or any later version. This 
#program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY or
#without any implied warranty. See the GNU General Public License for more details. 
#You should have received a copy of the GNU General Public License along with this software
#distribution; if not, you can download it for free at http://www.fsf.org/ 
#Questions marked with ANCOM makes an exception of above-written, as ANCOM is a romanian
#public authority(similar to FCC in USA) so any use of the official questions, other than
#in Read-Only way, is prohibited. 

# Made in Romania

# (c) YO6OWN Francisc TOTH, 2008 - 2020

#  troubleticket.cgi v 3.1.3
#  Status: working
#  This is a module of the online radioamateur examination program
#  "SimEx Radio", created for YO6KXP ham-club located in Sacele, ROMANIA
#  Made in Romania

# ch 3.1.3 charset=utf-8 added in generated html
# ch 3.1.2 filtering inputs for protection against cross-side-scripting
# ch 3.1.1 implementing Occam's Razor for input parameters
# ch 3.1.0 functions moved to ExamLib.pm
# ch 3.0.f solving https://github.com/6oskarwN/Sim_exam_yo/issues/14 - set a max size to db_tt
# ch 3.0.e deleted the old guestbook logging and displaying since is unused and could display internal logs to anyone.
# ch 3.0.d new transaction code simplified with epoch_time; timestamp_expired(); dienice; silent logging; SHA1 mac
# ch 3.0.c Admin: changed to YO6OWN
# ch 3.0.b the three stage of a ticket are clearly displayed [Nou][Vazut ...][Rezolvat]
# ch 3.0.a patch in a mailer when new complaints are registered; untested since no mail account possible; commented out
# ch 3.0.9 'ativan' added in the deny list, banned by awardspace.com
# ch 3.0.8 fixed POST that comes from special link in sim_verx.cgi in order to preserve &specials; and "overline"
# ch 3.0.7 <form> in <form> makes that blank record is saved if calculus is good but abandon is hit 
# ch 3.0.6 change window button to method="link" button  
# ch 0.1.5 GET changed to POST - devel
# ch 0.1.4 link to forumer elliminated by forumer migration to yuku. Ditching forum-based ticket handling.
# ch 0.1.3 link 404 to forumer, corrected. forumer was the error handling forum
# ch 0.1.2 linkuri aiurea catre kxp_index, corectat
# ch 0.1.1 made case-insensitive match for legal() dictionary and added 'proxy' to list of banned words - for sotw
# ch 0.1.0 older tickets not available any more as ZIP, but on the forum.
# ch 0.0.f fixed tt34-2 ANC renamed as ANCOM
# ch 0.0.e fixed tt34 ANRCTI renamed as ANC
# ch 0.0.d fixed trouble ticket 26
# ch 0.0.c solved troubleticket tt029
# ch 0.0.b troubleticket additional helping message 
# ch 0.0.a new feature added, online FR
# ch 0.0.9 new feature added without request - for internal ticket, nick == eXAM login
# ch 0.0.8 solved troubleticket20
# ch 0.0.7 links changed from white to red
# ch 0.0.6 troubleticket 19 solved
# ch 0.0.5 troubleticket 17 solved: Changed the targets of Abandon and OK - made context-sensitive
# ch 0.0.4 End of coding
# ch 0.0.3 Guestbook interface part1 implemented
# ch 0.0.2 human ID system changed to arithmetical operation
# ch 0.0.1 coding started

#$=====================================================================
use strict;
use warnings;
use lib '.';
use My::ExamLib qw(ins_gpl timestamp_expired compute_mac dienice);

my $get_type; #0 (anonymous) or 1(nick and prefilled) or undef(when we have transaction, or also attack cases)
my $get_nick; #nick for the guy who is writing
my $get_text; #submitted text
my $get_complaint; #the additional text inserted by user only when $get_type=1
my $get_answer; #authentication answer
my $get_trid; #transaction ID
my $trid; #transaction ID for anonymous, similar like for an exam
my $newtrid;
my @dbtt;   #this is the slurp variable

#### mailer patch v.3.0.a #############
#my $mailprog = '/usr/local/bin/sendmail'; #this is specific to my hoster
## Change the location above to wherever sendmail is located on your server.
#my $admin_email="curierul\@examyo.scienceontheweb.net";
## Change the address above to your e-mail address. Make sure to KEEP the \
#my $target_email="yo6own\@yahoo.com";
## Change the address above to your e-mail address. Make sure to KEEP the \
#### .end of mailer patch v 3.1.3 #####


#intermediate variables
my $get_aucpair;    #$question_auc:$answer_auc
my $question_auc;
my $answer_auc;

my $fline; #var used to read a file line by line
my $fline2;
#functii
sub legal; #returns 0 for obscene or illegal text and returns 1 for legal
sub aucenter(); #returns a string of following type - "text operatie:result"
sub new_transaction; #adds a tranzaction and returns a transaction ID;
sub get_transaction($); #daca tranzactia nu exista intoarce string vid; daca exista, sterge linia din fisier si intoarce un string care e chiar linia de tranzactie din fisier;
sub tran_refresh; #cleans expired transactions
sub addrec; #adds a record in db_tt troubletickets file

#BLOCK: Input
{
my $buffer;
my @pairs;
my $pair;
my $stdin_name;
my $stdin_value;


# Read input, POST or GET only

  if($ENV{'REQUEST_METHOD'} =~ m/POST/i)
         { read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'}); #POST data 
         }
  elsif($ENV{'REQUEST_METHOD'} =~ m/GET/i)
         { $buffer = $ENV{'QUERY_STRING'}; #GET data for type=0 request
         }
  else   {dienice("ERR20",0,\"null");} #request method other than GET/POST is discarded in non-descriptive way

#pre-process the POST data
$buffer=~ tr/+/ /;
$buffer=~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg; #special characters come like this

@pairs=split(/&/,$buffer ); #split the pairs in input; you don't know the exact order of the parameters

foreach $pair(@pairs) {
 ($stdin_name,$stdin_value) = split(/=/,$pair);

#if(defined $stdin_value) { #if input is malformed, pairs could be incomplete so stdin_value could be inexistent
# $stdin_value=~ tr/+/ /; #ideea e de a inlocui la loc + cu space
#this is needed because POST replaces every special char with its hex
# $stdin_value=~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg; #transforma %22 in =, %hex to char 
#2 times(once not enough to catch the stored XSS that will be active only after emerging from store)
# $stdin_value=~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg; #transforma %22 in =, %hex to char 
#                         }
#else { dienice("ERR20",0,\"null"); } #if undef $stdin_value

#Occam's razor:
#we try first to fill all and only the expected parameters - depending on the scenario,
#not all parameters are expected and might remain void/undef
#no value should be trusted since it can be malformed
 if($stdin_name eq 'type') { $get_type=$stdin_value;}   
 elsif($stdin_name eq 'nick'){$get_nick=$stdin_value;}  
 elsif($stdin_name eq 'subtxt'){$get_text=$stdin_value;}
 elsif($stdin_name eq 'complaint'){$get_complaint=$stdin_value;}
 elsif($stdin_name eq 'answer'){$get_answer=$stdin_value;}
 elsif($stdin_name eq 'transaction'){$get_trid=$stdin_value;}
                      } #end foreach pair
#end of Occam's razor

#any input parameter is not trusted, even if it's not a field of a form, it could be malformed.
#whitelist regexp  possible for: $get_type,$get_trid,$get_answer, $get_nick;
#$get_type: 0 and 1 legal, undef is legal, anything else not

if (defined $get_type) 
   {
    unless ( $get_type =~ m/^(0|1){1}$/ ) 
      {
      dienice("ERR01",0,\"illegal get_type, not 0/1 - type is: $get_type"); 
      }
    elsif ($get_type eq 1) {
                     unless(defined $get_nick && defined $get_text) { dienice ("ERR01",1,\"occam fail - troubleticket type 1 fails mandatory inputs: $buffer");}
                           }
   }


#$get_trid whitelist
if (defined $get_trid) 
   {
     unless ($get_trid =~ m/^[0-9,A-F]{6}_(\d{1,2}_){6}\d{3}_\d{1,2}_[0-9,a-f]{40}$/) 
     {
     dienice("ERR01",4,\"not compliant - transaction is:  $get_trid"); 
     }
   }
#$get_answer
if (defined $get_answer) 
   {   unless ($get_answer =~ m/^\d{1,2}$/) 
       {
       dienice("ERR01",0,\"not compliant - human answer is: $get_answer"); 
       }
   }

#$get_nick whitelist
if (defined $get_nick) 
   {
   unless($get_nick=~ m/^[a-zA-Z0-9_]{4,25}$/) #whitelist for nick same as for login 
       {
       dienice("ERR01",0,\"whitelist catch on nick: $get_nick"); 
       }
    }


#whitelist regexp not possible for: $get_text, $get_complaint
#$get_text blacklist
if (defined $get_text) 
   {
    if($get_text=~ m/(\%3C|<|&lt\;|\%3E|>|&gt\;)/i) #blacklist
       {
       $get_text=~ s/\r\l\n/<br>/g; #replace newline with <br>
       dienice("ERR01",4,\"blacklist catch on text: $get_text"); 
       }
    }

#$get_complaint blacklist
if (defined $get_complaint) 
   {
    if($get_complaint=~ m/((\%3C|<|&lt;).*(\%3E|>|&gt;)|\/)/i) #blacklist
       {
       $get_complaint=~ s/\r\l\n/<br>/g; #replace newline with <br>
       dienice("ERR01",4,\"blacklist catch on complaint: $get_complaint"); 
       }
    }



} #end input block




#########end of devel

#refresh the transactions in the transactions file
tran_refresh;

#generate the form, if $get_type is 0 or 1 or else
if (defined $get_type) #it means we have a first call
 {
  if($get_type eq 0) #external trouble ticket call; ignore any other possible parameter
  {
#call aucenter() that will generate human question and answer
 my $get_aucpair=aucenter();

 #split result from AUC in question and answer
($question_auc,$answer_auc)=split (/:/, $get_aucpair);

 #call new_transaction=add_transaction(type=1,AUC_result)
 $newtrid=new_transaction(0,$answer_auc);
# printf "new transaction: +%s+\n",$newtrid; #debug only

  print qq!Content-type: text/html\n\n!;
  print qq?<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n?; 
  print qq!<html>\n!;
  print qq!<meta charset=utf-8>\n!;
  print qq!<head>\n<title>colectare erori și sugestii</title>\n</head>\n!;
  print qq!<body bgcolor="#228b22" text="#7fffd4" link="blue" alink="blue" vlink="red">\n!;
  ins_gpl();
  print qq!<font size="-1">v 3.1.3</font>\n!; #version print for easy upload check
  print qq!<br>\n!;
 #se generate form by integrating $newtrid and $question_auc
  print qq!<center>\n<b>sistem de colecție erori</b>\n!;
  print qq!<form action="http://localhost/cgi-bin/troubleticket.cgi" method="post">\n!;
  print qq!<table width="90%" border="0">\n!;  #debug, border="0" originally

#ACTION: insert transaction ID in HTML page
{
  #my $extra=sprintf("%+06X",$trid); 
  print qq!<tr>\n!;
  print qq!<td colspan="3">\n!;
  print qq!<input type="hidden" name="transaction" value="$newtrid">\n!;
  print qq!</td>\n!;
  print qq!</tr>\n!;
  }

  print qq!<tr>\n!;
  print qq!<td colspan="3" align="left">\n!;
  print qq!Dacă umbli cu gânduri curate, știi că <font color="yellow">$question_auc</font>  egal !;
  print qq!<input type="text" name="answer" size="8"> (în cifre)<br><br>\n!;
  print qq!</td>\n!;
  print qq!</tr>\n!;

  print qq!<tr>\n!;
  print qq!<td align="left" valign="middle">\n!;
  print qq!<font color="yellow">nickname:</font>!;
  print qq!</td>\n!;
  print qq!<td align="left" colspan="2">\n!;
  print qq!<input type="text" name="nick" size="25">!;
  print qq!</td>\n!;
  print qq!</tr>\n!;

  print qq!<tr>\n!;
  print qq!<td valign="middle" align="left">\n!;
  print qq!<font color="yellow">Mesaj:</font>!;
  print qq!</td>\n!;

  print qq!<td align="left" colspan="2">\n!;
  print qq!<textarea name="subtxt" rows="5" cols="50" wrap="soft"></textarea>!;
  print qq!</td>\n!;
  print qq!</tr>\n!;

  print qq!<tr>\n!;
  print qq!<td valign="top">\n!;
  print qq!<center><INPUT type="submit"  value="Trimite"> </center>\n!;
  print qq!</td>\n!;
  print qq!<td valign="top">\n!;
  print qq!<center><INPUT type="reset"  value="Reset"> </center>\n!;
  print qq!</form>\n!;
  print qq!</td>\n!;

  print qq!<td valign="top">\n!;
  print qq!<form method="link" action="http://localhost/index.html">\n!;
  print qq!<center><INPUT TYPE="submit" value="Abandon"></center>\n!; 
  print qq!</form>\n!;
  print qq!</td>\n!;

  print qq!</tr>\n!;
  print qq!</table>\n!;

#se deschide fisierul cu inregistrari, read-only 
#se parcurge fisierul si se afiseaza toate inregistrarile de tickets
open(ttFILE,"<","db_tt");
seek(ttFILE,0,0);
@dbtt=<ttFILE>;   #we slurp the whole file into an array

print qq!<table border="1" width="90%">\n!;


my $backgnd;
$backgnd="\#d3d3d3";

#browse the records file backwards and display all tickets
for(my $i=($#dbtt+1)/4;$i>0;$i--)
{
chomp $dbtt[$i*4-3];
if($dbtt[$i*4-3] > 5)     #if it's a troubleticket record, only tickets are displayed, not 1-5 logs
{
if($backgnd eq "\#d3d3d3") {$backgnd="\#ADD8E6";}
else {$backgnd="\#d3d3d3";}
print qq!<tr>\n!;
print qq!<td bgcolor="$backgnd" align="left">\n!;

print qq!<font color="black"><b>$dbtt[$i*4-4]</b></font>&nbsp;!;  #print nick


   if ($dbtt[$i*4-3] eq 6) {print qq!<font color="red">[Nou]</font><font color="grey">=&gt;[Citit de admin]=&gt;[Rezolvat]</font>!;}
elsif ($dbtt[$i*4-3] eq 7) {print qq!<font color="blue">[Citit de admin]</font><font color="grey">=&gt;[Rezolvat]</font>!;}
elsif ($dbtt[$i*4-3] eq 8) {print qq!<font color="green">[Rezolvat]</font>!;}

##doubled
my $toprint = $dbtt[$i*4-2];

#print qq!<font color="black" size="-1">$dbtt[$i*4-2]</font><br>\n!; #debug: black is orange
print qq!<font color="black" size="-1">$toprint</font><br>\n!; #debug: black is orange

unless ($dbtt[$i*4-1] eq "\n") {
print qq!<font color="blue" size="-1">YO6OWN: $dbtt[$i*4-1]</font><br>!;
                               }
print qq!</td>\n!;
print qq!</tr>\n!;                              
} #.end it's a ticket record, 1-5 logs are not displayed
} #.end for/4
#----------------------

print qq!</table>\n!;

print qq!</center>\n!;

 print qq!</body>\n</html>\n!;
 #se inchide fisierul cu inregistrari
close(ttFILE);
 
  
  }
#end of case when $type=0, new ticket, anonymous.
#start the case of prefilled ticket
  elsif($get_type eq 1) #internal trouble ticket first call
  {
#call humanity check precalculate, ,the AUC
 my $get_aucpair=aucenter();

 #se splituieste rezultatul lui AUC in intrebare si raspuns
($question_auc,$answer_auc)=split (/:/, $get_aucpair);

 #se apeleaza new_transaction=add_transaction(type=1,AUC_result)
 $newtrid=new_transaction(1,$answer_auc);
# printf "new transaction: +%s+\n",$newtrid; #debug only

 #se scrie header html
  print qq!Content-type: text/html\n\n!;
  print qq?<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n?; 
  print qq!<html>\n!;
  print qq!<meta charset=utf-8>\n!;
  print qq!<head>\n<title>colectare erori și sugestii</title>\n</head>\n!;
  print qq!<body bgcolor="#228b22" text="#7fffd4" link="blue" alink="blue" vlink="red">\n!;
  ins_gpl();
  print qq!<font size="-1">v 3.1.3</font>\n!; #version print for easy upload check
  print qq!<br>\n!;
 #se genereaza formularul integrand $newtrid si $question_auc
print qq!<center>\n<b>sistem de colecție erori</b>\n!;
print qq!<form action="http://localhost/cgi-bin/troubleticket.cgi" method="post">\n!;
print qq!<table width="90%" border="0">\n!;

#ACTION: inserare transaction ID in pagina HTML
{
#my $extra=sprintf("%+06X",$trid);
print qq!<tr>\n!;
print qq!<td colspan="2">\n!;
print qq!<input type="hidden" name="transaction" value="$newtrid">\n!;
print qq!</td>\n!;
print qq!</tr>\n!;
}

print qq!<tr>\n!;
print qq!<td colspan="3" align="left">\n!;
print qq!Dacă umbli cu gânduri curate, știi că <font color="yellow">$question_auc</font>  egal !;
print qq!<input type="text" name="answer" size="8"> (în cifre)<br><br>\n!;
print qq!</td>\n!;
print qq!</tr>\n!;

print qq!<tr>\n!;
print qq!<td align="left" valign="middle">\n!;
print qq!<font color="yellow">nickname:</font>!;
print qq!</td>\n!;
print qq!<td align="left" colspan="2">\n!;
print qq!$get_nick <input type="hidden" name="nick" value="$get_nick">!; #nick supposed to be eXAM login but don't take it as granted, can be malformed.
print qq!</td>\n!;
print qq!</tr>\n!;

print qq!<tr>\n!;
print qq!<td valign="middle" align="left">\n!;
print qq!<font color="yellow">Mesaj:</font>!;
print qq!</td>\n!;


print qq!<td align="left" colspan="2">\n!;

#print qq!$get_text<br>\n!; #debug
print qq!<input type="hidden" name="subtxt" value=\"$get_text\">\n!;
my $toprint=$get_text;
#asta e o evaluare, de vazut daca chiar e nevoie, si de vazut daca asta e inainte de write in fisier sau inainte de resend to troubleticket.cgi
#normal nu e nevoie deoarece s-a facut deja o conversie hex2char
#$toprint=~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg; #transforma %22 in =, %hex to char #poate aici afecta inainte pe &radic, nu mai e cazul;
print qq!$toprint<br>\n!; #debug

print qq!<textarea name="complaint" rows="5" cols="50" wrap="soft">explicația ta aici</textarea>!;
#print qq!<textarea name="subtxt" rows="5" cols="50" wrap="soft">$get_text</textarea>!;
print qq!</td>\n!;
print qq!</tr>\n!;

print qq!<tr>\n!;
print qq!<td valign="top">\n!;
print qq!<center><INPUT type="submit"  value="Trimite"> </center>\n!;
print qq!</td>\n!;
print qq!<td valign="top">\n!;
print qq!<center><INPUT type="reset"  value="Reset"> </center>\n!;
print qq!</form>\n!;
print qq!</td>\n!;

print qq!<td valign="top">\n!;
print qq!<form method="link" action="http://localhost/index.html">\n!;
print qq!<center><INPUT TYPE="submit" value="Abandon"></center>\n!; 
print qq!</form>\n!;
print qq!</td>\n!;

print qq!</tr>\n!;

print qq!</table>\n!;

print qq!</center>\n!;
 #se inchide html
  print qq!</body>\n</html>\n!;
 
  }
# end of type=1, prefilled ticket


# code coverage dead branch, this case is treated at the beginning
# else {dienice("ERR01",1,\"received type is not 0 or 1:  $get_type");} #hacker attack, type is only  0,1

 } #.end first call solve

else #it's not a first call, it must have a transaction-based handling
{
if ((defined $get_trid) && ($get_nick =~ /\w+/) && ($get_text =~ /\w+/))  #once ore more non-whitespace characters
{

#dienice("ERR19",1,\"gettrid $get_trid getnick $get_nick gettext $get_text"); #debug silent logging

my $tridstring;
my $trid_type;
my $trid_answer;

#daca exista, adaugam complaint la text problema
if(defined $get_complaint ) {$get_text = "$get_text (varianta) $get_complaint";}
$get_text=~ s/\r\l\n/<br>/g; #workaround de sfarsit de inlocuire enter cu <br>

$tridstring=get_transaction($get_trid);
if($tridstring =~ m/:/) #transaction existed because the check consumed it
{
($trid_type,$trid_answer)= split (/:/,$tridstring);

#check human test
if($trid_answer eq $get_answer) 
{
if((legal($get_text) eq 1) and (legal($get_nick)))
{
 my$stringtime=localtime;
 $get_text="<font color=green> ($stringtime) </font><br>$get_text";

if(($trid_type eq 0) or ($trid_type eq 1)) #general troubleticket form 
                    {addrec($get_nick,6,$get_text); #6 is ticket, 1 to 5 are threat levels for internal logging
                    print qq!<center>\n!;
                    print qq!<INPUT TYPE="submit" value="OK"><br>\n!;
                    print qq!Hint: Poți să revii de aici în pagina anterioară pentru a propune o nouă notificare, apăsând de două ori săgeata înapoi  <==  în browserul web. \n!;
                    print qq!</center>\n!;
                    print qq!</form>\n!; 
                    print qq!</body>\n</html>\n!;
                    }

                    else {dienice("ERR01",0,\"trid_type nu e 0 sau 1, ciudat"); } 
}
#else there are words in the banned list
else {
   dienice("ERR01",1,\"illegal input catch by white or blacklist: null"); 
      }
                                                      
}
# $trid_answer not same as $get_answer so not human
else {
   dienice("ttERR04",1,\"$get_answer"); 
      }


}
#transaction used or expired
else {
   dienice("ERR02",1,\"transaction used or expired"); 
     }


}
#one or more whitespace characters, see if() line 484
else {
   dienice("ttERR06",1,\"null"); 
      }
} 
 
 
 
#----100%------subrutina generare random number
sub random_int($)
	{
	
	my ($max)=@_;

       return int rand($max);
	}
#---legality of a string---
#--returns 1 for legal
#--returns 0 for illegal
sub legal
{
#lower-case dictionary, enough
#it's a black list, which is not a best idea. whitelist is better but awardnet 
#implements it as blacklist

my @blackDictionary=(
              'regexp',  #regular expression should not be allowed
              'sex',
              'porn',    #denied by awardspace.com
              'proxy',   #denied by awardspace.com
              'ativan'    #denied by awardspace.com

            );
my $inputstring;
($inputstring)=@_;
my $iter;
my $legall;
$legall=1;#init to legal

foreach $iter (@blackDictionary)
{
if($inputstring =~ m/$iter/i) #forces case-insensitive match
{ $legall=0; #should be the exit from loop, not from if but the list is still short
}

}#.end foreach

 return($legall);

}#.end sub
#------------------------
#Authentication center function
#exemple: dupa 1,2,3 si 4 urmeaza:5

sub aucenter()
{
my $operand1=random_int(20);
my $operand2=random_int(20);
my $suma=$operand1+$operand2;
return("$operand1 adunat cu $operand2:$suma");
}

#--------------------
sub tran_refresh
{
my @tridfile;
my @livelist=();
my @linesplit;
my $i;
#my $j;

open(transactionFILE,"+< tt_transaction");
seek(transactionFILE,0,0);		#go to the beginning
@tridfile = <transactionFILE>;		#slurp file into array

#ACTION: refresh transaction list, delete expired transactions,
# transaction pattern in file:
# A00125_0_46_53_23_4_9_118_33_697bff0413fe06cb49f8875b7461603bc500fa6c #first 0 is type of trouble 0 = ticket, 33 is result of humanity check


unless($#tridfile == 0) 		#unless transaction list is empty (but transaction exists on first line)
{ #.begin unless
   for($i=1; $i<= $#tridfile; $i++)	#check all transactions 
  {
   @linesplit=split(/_/,$tridfile[$i]);
#   chomp $linesplit[8]; #\n is deleted
  if (timestamp_expired($linesplit[2],$linesplit[3],$linesplit[4],$linesplit[5],$linesplit[6],$linesplit[7]) > 0 ) {} #if timestamp expired do nothi$
  else {@livelist=(@livelist, $i);} #not expired, refresh it
  } #.end for

} #.end unless

my @extra=();
@extra=(@extra,$tridfile[0]);		#transactionID it's always alive

foreach $i (@livelist) {@extra=(@extra,$tridfile[$i]);} #reconstitute @tridfile content
@tridfile=@extra;

#Action: rewrite transaction file
truncate(transactionFILE,0);
seek(transactionFILE,0,0);				#go to beginning of transactionfile
#rewrite transaction file
for($i=0;$i <= $#tridfile;$i++)
{
printf transactionFILE "%s",$tridfile[$i]; #we have \n at the end of each element
}

close(transactionFILE);

} #.end sub tran_refresh


#---------------------
sub new_transaction
{
my ($type_code,$aucresult)=@_;
my @tridfile;


#my @linesplit;
my $i;
#my $j;
my $hexi;

#open transaction file
open(transactionFILE,"+< tt_transaction");

seek(transactionFILE,0,0);		#go to the beginning
@tridfile = <transactionFILE>;		#slurp file into array


# transaction pattern in file:
# A000D6_0_10_10_23_3_9_118_16_sha1sha1sha1 #first 0 is type of trouble 0 = ticket, 16 is result of humanity check



#Action: generate new transaction
$trid=$tridfile[0];
chomp $trid;						#eliminate \n
$trid=hex($trid);		#convert string to numeric

if($trid == 0xFFFFFF) {$tridfile[0] = sprintf("%+06X\n",0);}
else { $tridfile[0]=sprintf("%+06X\n",$trid+1);}                #cyclical increment 000000 to 0xFFFFFF

#print qq!generate new transaction<br>\n!;
my $epochTime = time();
#CUSTOM
my $epochExpire = $epochTime + 900; #15 minutes lifetime = 900 sec
my ($exp_sec, $exp_min, $exp_hour, $exp_day,$exp_month,$exp_year) = (gmtime($epochExpire))[0,1,2,3,4,5];


#print to screen the entry in the transaction list
$hexi= sprintf("%+06X",$trid);
my $entry = "$hexi\_$type_code\_$exp_sec\_$exp_min\_$exp_hour\_$exp_day\_$exp_month\_$exp_year\_$aucresult\_";
#print qq!mio entry: $entry <br>\n!; #debug
my $heximac = compute_mac($entry); #compute sha1 MessageAuthentication Code
$entry= "$entry$heximac\n"; #the full transaction id


@tridfile=(@tridfile,$entry); 				#se adauga tranzactia in array
#print "Trid-array after adding new-trid: @tridfile[0..$#tridfile]<br>\n"; #debug


#Action: rewrite transaction file
truncate(transactionFILE,0);
seek(transactionFILE,0,0);				#go to end of transactionfile
for($i=0;$i <= $#tridfile;$i++)
{
printf transactionFILE "%s",$tridfile[$i]; #we have \n at the end of each element
}

#close transactionfile
close(transactionFILE);
#return new trid
chomp($entry); #it has \n so it can be written in file
return($entry);
}#.end sub add_transaction
#================================================================
#================================================================
#------------------------------------------------
#daca tranzactia nu exista intoarce string vid; 
#daca exista, sterge linia din fisier si intoarce un string care e "type:auc_result"
sub get_transaction($) 
{
my ($sub_trid)=@_;       #input data
my $entry;  #output data
my @tridfile;
my @linesplit;
my @livelist=();
my $i;

#$sub_trid must be checked first if it has valid trailing MAC
@linesplit=split(/_/,$sub_trid);
#$linesplit[9] is the mac

unless(defined($linesplit[9])) {dienice ("ttERR08",1,\$sub_trid); } # unstructured trid

#first a check trat submitted trid is valis for hash
$entry="$linesplit[0]\_$linesplit[1]\_$linesplit[2]\_$linesplit[3]\_$linesplit[4]\_$linesplit[5]\_$linesplit[6]\_$linesplit[7]\_$linesplit[8]\_";
my $heximac= compute_mac($entry);
$entry='';
unless ($linesplit[9] eq $heximac) {dienice("ERR01",4,\"transaction id sha1 mismatch: $linesplit[9]VsV$heximac");}

#open transaction file
open(transactionFILE,"+< tt_transaction");
seek(transactionFILE,0,0);		#go to the beginning
@tridfile = <transactionFILE>;		#slurp file into array

unless($#tridfile == 0) 		#unless transaction list is empty (but transaction nmber exists on first line)
{ #.begin unless

for($i=1;$i <= $#tridfile;$i++)
{
my $string = $tridfile[$i];
chomp($string);
@linesplit=split(/_/,$string);
if($string eq $sub_trid) { 
                            $entry="$linesplit[1]:$linesplit[8]";
                         } #transaction found and ingested
else { @livelist=(@livelist,$i); }
#dienice("ERR19",5,\"step3\:$string eq $sub_trid\?$entry\;");#debug logging

}


} #.end unless

#Action: rewrite transaction file
my @extra=();
@extra=(@extra,$tridfile[0]);		#transactionID it's always alive
foreach $i (@livelist) {@extra=(@extra,$tridfile[$i]);} #reconstitute @tridfile content
@tridfile=@extra;

truncate(transactionFILE,0);
seek(transactionFILE,0,0);				#go to beginning of transactionfile
#rewrite transaction file
for($i=0;$i <= $#tridfile;$i++)
{
printf transactionFILE "%s",$tridfile[$i]; #we have \n at the end of each element
}

close(transactionFILE);

return($entry);

}#.end sub
#----------------------

sub addrec
{
my $sub_nick;
my $sub_code;
my $sub_text;
($sub_nick,$sub_code,$sub_text)=@_;

#### patch for mailer implementation from v 3.1.3 ######
#open (MAIL, "|$mailprog -t") || die "Can't open $mailprog!\n";
#print MAIL "From: $admin_email\n";
#print MAIL "To: $target_email\n";
#print MAIL "Subject: new complaint filed\n\n";
#print MAIL <<to_the_end;
#new complaint was filed in
#to_the_end
#close (MAIL);
############ patch end #########

open(recFILE,"+< db_tt");
#goto end for append
seek(recFILE,0,2); #should be end of file
#append new record
printf recFILE "%s\n%s\n%s\n\n",$sub_nick,$sub_code,$sub_text; 

close(recFILE);
print qq!Content-type: text/html\n\n!;
print qq?<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n?; 
print qq!<html>\n!;
print qq!<meta charset=utf-8>\n!;
print qq!<head>\n<title>colectare erori și sugestii</title>\n</head>\n!;
print qq!<body bgcolor="#228b22" text="#7fffd4" link="blue" alink="blue" vlink="red">\n!;
ins_gpl();
print qq!v 3.1.3\n!; #version print for easy upload check
print qq!<br>\n!;
print qq!<h1 align="center">Adăugare reușită.</h1>\n!;
print qq!<form method="link" action="http://localhost/index.html">\n!;
#---------html page should finish here, but HTML code will continue after returning from function so that it prints different targets
}
