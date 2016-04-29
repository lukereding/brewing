# brewing

I'm using this repo to keep track of changes I make to `brew.py`, the Python script I use to regulate the temperature of my fermenter.

#### usage
Something like:

`sudo nohup python -u brew.py dubbelTrouble 80 24 78 12 75 12 72 12 70 60 75 24 80 24 >> brewPySTDOUTDubbelTrouble.log 2>&1 &`

The `nohup` is necessary so that you can `logout` of your pi and still have the program running. 

`dubbelTrouble` is the name you want to give your brew.

The list of numbers (there could be a better way to do this, but it works for now) is a series of ordered pairs, where the first number is the temperature you want to maintain and the second number is the number of hours you want to maintain it for.

The `-u` flag is important to insure Python runs unbuffered; otherwise the program will occassionally cut out after a couple weeks and you will be sad and confused. 

Note also that you should change the email addresses in the script if you want to receive daily updates on the temperature profile of your brew. The graph attached in the email looks something like this:

![temperature graph](dubbel%20trouble.pdf "example temperature graph emailed to the user")
