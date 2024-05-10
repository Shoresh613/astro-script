from kerykeion import AstrologicalSubject, KerykeionChartSVG

first = AstrologicalSubject("Jack", 1990, 6, 15, 15, 15, "Roma")
second = AstrologicalSubject("Jane", 1991, 10, 25, 21, 00, "Roma")

# Set the type, it can be Natal, Synastry or Transit

name = KerykeionChartSVG(first, chart_type="Synastry", second_obj=second)
name.makeSVG("./synastry.svg")
print(len(name.aspects_list))

#> Generating kerykeion object for Jack...
#> Generating kerykeion object for Jane...
#> Jack birth location: Roma, 41.89193, 12.51133
#> SVG Generated Correctly
#> 38
