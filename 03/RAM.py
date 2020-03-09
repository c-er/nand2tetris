import sys

small = sys.argv[1]
tot = sys.argv[2]
print("DMux4Way(in=load, sel=address[0..1], a=l{}, b=l{}, c=l{}, d=l{});".format(*list(range(4))))

for i in range(4):
  print("{}(in=in, load=l{}, address=address[2..{}], out=out{});".format(small, i, tot, i))

print("Mux4Way16(a=out{}, b=out{}, c=out{}, d=out{}, sel=address[0..2], out=out);".format(*list(range(4))))
